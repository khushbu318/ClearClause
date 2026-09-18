"""Frontend UI component package."""

from frontend.ui.clause_card import render_clause_card
from frontend.ui.processing_status import render_processing_status
from frontend.ui.theme import (
    ACCENT_COLOR,
    GLOBAL_CSS,
    LABEL_COLORS,
    PRIMARY_COLOR,
    PRIORITY_COLORS,
    apply_custom_css,
)

__all__ = [
    "apply_custom_css",
    "PRIMARY_COLOR",
    "ACCENT_COLOR",
    "PRIORITY_COLORS",
    "LABEL_COLORS",
    "GLOBAL_CSS",
    "render_clause_card",
    "render_processing_status",
]
