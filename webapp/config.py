"""Centralized constants and shared UI helpers for the webapp."""

import streamlit as st

# ---------------------------------------------------------------------------
# Chat settings
# ---------------------------------------------------------------------------
MIN_TURNS = 2
MAX_TURNS = 6
MIN_INTERACTION_TIME = 540  # seconds
WORDS_LIMIT = 150

AGENT_MODEL = "openai/gpt-4.1-mini"   # used by therapy_system agent routing (needs prefix)
DETECTION_MODEL = "gpt-4.1-mini"      # used by direct OpenAI API calls
PERSONA_MODEL = "gpt-4.1-mini"        # used by direct OpenAI API calls

# ---------------------------------------------------------------------------
# Data file paths (relative to project root)
# ---------------------------------------------------------------------------
PERSONA_CSV = "persona_info_hierarchy.csv"
POSTHOC_CSV = "posthoc_survey.csv"
UNN_INFO_CSV = "unn_info.csv"

# ---------------------------------------------------------------------------
# External URLs
# ---------------------------------------------------------------------------
PROLIFIC_URL = "https://app.prolific.com/submissions/complete?cc=CFUSO5QT"

# ---------------------------------------------------------------------------
# Survey display sizes
# ---------------------------------------------------------------------------
SURVEY_HEADER_SIZE = 24
SURVEY_LABEL_SIZE = 20
SURVEY_OPTION_SIZE = 14

MIN_REASONING_WORDS = 10

# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def disable_copy_paste():
    """Inject CSS + JS to prevent copy/paste in text inputs and text areas."""
    st.components.v1.html("""
        <style>
        * {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        body { -webkit-touch-callout: none; }
        .stTextArea textarea {
            user-select: none !important;
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
        }
        </style>
        <script>
        function disableCopyPaste() {
            const els = parent.document.querySelectorAll('.stTextInput input, .stTextArea textarea');
            els.forEach(el => {
                el.addEventListener('copy', e => e.preventDefault());
                el.addEventListener('cut', e => e.preventDefault());
                el.addEventListener('paste', e => e.preventDefault());
                el.addEventListener('contextmenu', e => e.preventDefault());
                el.addEventListener('keydown', e => {
                    if ((e.ctrlKey || e.metaKey) && ['c','v','x'].includes(e.key))
                        e.preventDefault();
                });
            });
        }
        disableCopyPaste();
        setTimeout(disableCopyPaste, 500);
        new MutationObserver(disableCopyPaste)
            .observe(parent.document.body, {childList: true, subtree: true});
        </script>
    """, height=0)

    st.markdown("""
        <style>
        * {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        body { -webkit-touch-callout: none; }
        .survey-heading { font-size: 30px !important; }
        .survey-text    { font-size: 20px !important; }
        .survey-reveal  { font-size: 14px !important; }
        </style>
    """, unsafe_allow_html=True)
