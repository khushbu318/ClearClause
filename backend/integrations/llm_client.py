"""LLM integration client using OpenRouter API with JSON schema enforcement and retry logic."""

import json
import os
import re
import time
from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    """Base exception for LLM call failures."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class SchemaValidationError(LLMError):
    """Raised when LLM response fails Pydantic schema validation after retries."""
    pass


def _extract_json_block(text: str) -> str:
    """Extract JSON block from Markdown backticks or surrounding text preamble."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()

    # Find boundaries of valid JSON object/array
    start_idx = -1
    for i, ch in enumerate(text):
        if ch in ("{", "["):
            start_idx = i
            break

    end_idx = -1
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ("}", "]"):
            end_idx = i
            break

    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        return text[start_idx : end_idx + 1]

    return text


class LLMClient:
    """Wrapper for calling LLM endpoints with structured JSON output validation."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL, timeout: int = 45):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model
        self.timeout = timeout

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[T] | None = None,
        temperature: float = 0.1,
        max_retries: int = 1,
    ) -> dict[str, Any]:
        """Send a completion request and parse/validate response against Pydantic schema if provided."""
        if not self.api_key:
            try:
                import streamlit as st
                if "OPENROUTER_API_KEY" in st.secrets:
                    self.api_key = st.secrets["OPENROUTER_API_KEY"]
            except Exception:
                pass

        if not self.api_key:
            logger.error("OPENROUTER_API_KEY is missing!")
            raise LLMError(
                "OPENROUTER_API_KEY is not set. Please set it in environment variables or Streamlit secrets."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://clearclause.app",
            "X-Title": "ClearClause",
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"} if schema else None,
        }

        schema_name = schema.__name__ if schema else "None"
        prompt_len = len(system_prompt) + len(user_prompt)
        logger.info(f"Sending LLM request [model={self.model}, schema={schema_name}, prompt_chars={prompt_len}]")

        attempt = 0
        last_error = None
        start_time = time.time()

        while attempt <= max_retries:
            attempt += 1
            call_start = time.time()
            try:
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                elapsed_call = time.time() - call_start

                if response.status_code != 200:
                    logger.warning(
                        f"Attempt {attempt} failed [status={response.status_code}, elapsed={elapsed_call:.2f}s]: {response.text[:200]}"
                    )
                    error_msg = f"OpenRouter API returned status {response.status_code}: {response.text}"
                    last_error = LLMError(error_msg)
                    if response.status_code in (429, 502, 503, 504) and attempt <= max_retries:
                        continue
                    raise last_error

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    logger.error(f"Attempt {attempt} returned empty choices payload.")
                    raise LLMError("LLM response contained no choices.")

                raw_content = choices[0].get("message", {}).get("content", "")
                json_str = _extract_json_block(raw_content)

                try:
                    parsed_json = json.loads(json_str)
                except json.JSONDecodeError as exc:
                    logger.warning(f"Attempt {attempt} returned non-JSON string [len={len(raw_content)}]: {exc}")
                    last_error = SchemaValidationError(f"Invalid JSON returned: {exc}. Content: {raw_content[:200]}")
                    if attempt <= max_retries:
                        messages.append({"role": "assistant", "content": raw_content})
                        messages.append({"role": "user", "content": "Your previous response was not valid JSON. Please return ONLY a valid JSON object matching the requested schema."})
                        payload["messages"] = messages
                        continue
                    raise last_error from exc

                if schema:
                    try:
                        validated_model = schema.model_validate(parsed_json)
                        total_time = time.time() - start_time
                        logger.info(
                            f"LLM request succeeded [schema={schema_name}, total_time={total_time:.2f}s]"
                        )
                        return validated_model.model_dump()
                    except ValidationError as val_err:
                        logger.warning(f"Attempt {attempt} schema validation failed: {val_err}")
                        last_error = SchemaValidationError(f"Pydantic validation failed: {val_err}")
                        if attempt <= max_retries:
                            messages.append({"role": "assistant", "content": raw_content})
                            messages.append({"role": "user", "content": f"Output failed schema validation: {val_err}. Please fix the fields and return a valid JSON object."})
                            payload["messages"] = messages
                            continue
                        raise last_error from val_err

                total_time = time.time() - start_time
                logger.info(f"LLM request succeeded [total_time={total_time:.2f}s]")
                return parsed_json

            except requests.Timeout as exc:
                elapsed_call = time.time() - call_start
                logger.error(f"Attempt {attempt} timed out after {elapsed_call:.2f}s")
                last_error = LLMTimeoutError(f"LLM request timed out after {self.timeout}s")
                if attempt <= max_retries:
                    continue
                raise last_error from exc
            except requests.RequestException as exc:
                logger.error(f"Attempt {attempt} network error: {exc}")
                last_error = LLMError(f"Network error calling OpenRouter: {exc}")
                if attempt <= max_retries:
                    continue
                raise last_error from exc

        if last_error:
            raise last_error
        raise LLMError("LLM call failed after retries.")
