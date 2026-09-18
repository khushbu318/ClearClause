"""Streamlit UI component to show staged execution status for multi-step agent graphs."""

import streamlit as st

STAGES = [
    "📥 Document received & parsed",
    "🔍 Generating page/vector index",
    "⚡ Extracting key legal clauses",
    "💡 Synthesizing Clause Cards",
    "📝 Generating whole-document analysis",
]


def render_processing_status(current_stage_idx: int):
    """Render a progress status indicator."""
    current_stage_idx = max(0, min(current_stage_idx, len(STAGES) - 1))
    progress = (current_stage_idx + 1) / len(STAGES)

    st.progress(progress)
    st.info(f"**Status:** {STAGES[current_stage_idx]}")
