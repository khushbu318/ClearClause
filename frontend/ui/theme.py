"""Theme constants, color tokens, and custom CSS styling for ClearClause UI."""

import streamlit as st

PRIMARY_COLOR = "#1E3A5F"      # Deep Navy Blue
ACCENT_COLOR = "#0E9B8A"       # Teal Accent
BG_LIGHT = "#F8FAFC"           # Off-white / light slate background

PRIORITY_COLORS = {
    "High": {"text": "#92400E", "bg": "#FEF3C7", "border": "#F59E0B", "badge": "#D97706"},
    "Medium": {"text": "#1E40AF", "bg": "#EFF6FF", "border": "#60A5FA", "badge": "#2563EB"},
    "Low": {"text": "#374151", "bg": "#F3F4F6", "border": "#9CA3AF", "badge": "#4B5563"},
    "FYI": {"text": "#065F46", "bg": "#ECFDF5", "border": "#34D399", "badge": "#059669"},
}

LABEL_COLORS = {
    "Review carefully": "#D97706",
    "Potentially important": "#2563EB",
    "Standard": "#4B5563",
    "Beneficial": "#059669",
    "Unclear": "#DC2626",
}

GLOBAL_CSS = """
<style>
.stApp {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
.clause-card {
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    background-color: #ffffff;
    border-left: 6px solid #1E3A5F;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.15s ease-in-out;
}
.clause-card-high {
    border-left-color: #D97706 !important;
    background-color: #FFFBEB;
}
.clause-card-medium {
    border-left-color: #2563EB !important;
    background-color: #F0F9FF;
}
.clause-card-low {
    border-left-color: #6B7280 !important;
    background-color: #F9FAFB;
}
.clause-card-fyi {
    border-left-color: #059669 !important;
    background-color: #ECFDF5;
}
.priority-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #ffffff;
}
.badge-high { background-color: #D97706; }
.badge-medium { background-color: #2563EB; }
.badge-low { background-color: #4B5563; }
.badge-fyi { background-color: #059669; }

.disclaimer-banner {
    background-color: #F1F5F9;
    border: 1px solid #CBD5E1;
    color: #475569;
    padding: 10px 16px;
    border-radius: 6px;
    font-size: 0.85rem;
    margin-bottom: 20px;
}
</style>
"""


def apply_custom_css():
    """Inject custom styling for cards, typography, and crisp layout."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
