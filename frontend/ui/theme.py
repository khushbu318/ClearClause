# Colors
PRIMARY = "#0E9B8A"          # teal — brand primary
SECONDARY = "#1E3A5F"        # deep blue — brand secondary
ACCENT_HIGH = "#F59E0B"      # amber — High priority clause cards ONLY
ACCENT_ERROR = "#EF4444"     # red — error states ONLY
BG_MAIN = "#0F1923"          # main background
BG_CARD = "#1A2838"          # card / secondary background
TEXT_PRIMARY = "#E8EDF2"     # primary text
TEXT_MUTED = "#8B9CB3"       # muted / secondary text
BORDER = "#2A3F55"           # card borders

# Priority → color mapping
PRIORITY_COLORS = {
    "High": "#F59E0B",    # amber
    "Medium": "#3B82F6",  # blue
    "Low": "#6B7280",     # gray
    "FYI": "#10B981",     # green
}

# Review label → badge color
LABEL_COLORS = {
    "Review carefully": "#EF4444",
    "Potentially important": "#F59E0B",
    "Standard": "#6B7280",
    "Beneficial": "#10B981",
    "Unclear": "#8B5CF6",
}

# Streamlit custom CSS injected on every page load
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit default menu and footer in prod */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Card base */
.cc-card {
    background: #1A2838;
    border: 1px solid #2A3F55;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.2s ease;
}
.cc-card:hover {
    box-shadow: 0 4px 20px rgba(14, 155, 138, 0.15);
}

/* Priority badge */
.cc-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* Section divider */
.cc-divider {
    border: none;
    border-top: 1px solid #2A3F55;
    margin: 0.75rem 0;
}

/* Step status */
.cc-step-done { color: #10B981; }
.cc-step-active { color: #0E9B8A; font-weight: 600; }
.cc-step-pending { color: #8B9CB3; }
</style>
"""
