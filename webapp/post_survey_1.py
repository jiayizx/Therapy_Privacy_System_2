"""Post Survey Part 1: experience and empathy ratings (hardcoded)."""

import streamlit as st

from firebase_utils import save_survey_one


# ── CSS ──────────────────────────────────────────────────────────────────

def _apply_styles():
    st.markdown("""
        <style>
        /* Section headers */
        .section-header {
            font-size: 22px;
            font-weight: 600;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
            padding-bottom: 0.4em;
            border-bottom: 2px solid #e0e0e0;
        }

        /* Question card */
        .question-card {
            background: var(--secondary-background-color, #f8f9fa);
            border-radius: 10px;
            padding: 1em 1.2em 0.6em 1.2em;
            margin-bottom: 0.2em;
        }
        .question-label {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 0;
        }
        .question-number {
            color: #636efa;
            font-weight: 700;
        }

        /* Horizontal radio buttons – more breathing room */
        .stRadio > div[role="radiogroup"] {
            flex-direction: row !important;
            gap: 0.6em;
            flex-wrap: wrap;
        }
        .stRadio > div[role="radiogroup"] label {
            font-size: 14px !important;
        }
        </style>
    """, unsafe_allow_html=True)


# ── Questions ────────────────────────────────────────────────────────────

AGREE_STATEMENTS = [
    "I trust this AI chatbot to be reliable",
    "I do not feel totally safe providing personal private information over this chatbot",
    "I think this AI chatbot is persuasive",
    "I enjoyed the therapy session",
]
AGREE_OPTIONS = ["Select an option", "disagree", "slightly disagree", "neutral", "slightly agree", "agree"]

EMPATHY_STATEMENTS = [
    "I found that Alex's condition affected my mood",
    "I was very affected by the emotions in Alex's story",
    "I actually felt Alex's distress",
    "I experienced Alex's feelings as if they were my own",
    "I found myself imagining how I would feel in Alex's situation",
    "I found myself imagining myself in Alex's shoes",
    "I found myself trying to imagine how things looked to Alex",
    "I found myself trying to imagine what Alex was experiencing",
    "I feel confident that I could accurately describe Alex's experience from his/her point of view",
    "I found it easy to understand Alex's reactions",
    "I found it easy to see how the situation looked from Alex's point of view",
    "Even though Alex's life experiences are different to mine, I can really see things from his/her perspective",
    "I am sure that I know how Alex was feeling",
    "I feel confident that I could accurately describe how Alex felt",
]
EMPATHY_OPTIONS = ["Select an option", "completely untrue", "mostly untrue", "neutral", "mostly true", "completely true"]

ALL_STATEMENTS = AGREE_STATEMENTS + EMPATHY_STATEMENTS
_N_QUESTIONS = len(ALL_STATEMENTS)


# ── Helpers ──────────────────────────────────────────────────────────────

def _render_question(num: int, statement: str, options: list, qkey: str):
    """Render a single question inside a styled card, with radio options below."""
    st.markdown(
        f'<div class="question-card">'
        f'<p class="question-label"><span class="question-number">Q{num}.</span> {statement}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.session_state.survey_response[qkey] = st.radio(
        label=f"Q{num}",
        options=options,
        index=options.index(st.session_state.survey_response[qkey]),
        key=qkey,
        horizontal=True,
        label_visibility="collapsed",
    )


# ── Main ─────────────────────────────────────────────────────────────────

def post_survey_one():
    _apply_styles()

    if "prolific_id" not in st.session_state or not st.session_state.prolific_id:
        st.warning("Please go back to the main page and enter your Prolific ID.")
        st.stop()

    if st.session_state.get("phase") != "post_survey":
        st.warning("Please complete the chat session before proceeding to the survey.")
        st.stop()

    if st.session_state.get("responses_submitted"):
        st.write("You have already submitted your responses. Thank you!")
        return

    if "survey_response" not in st.session_state:
        st.session_state.survey_response = {f"Q{i}": "Select an option" for i in range(1, _N_QUESTIONS + 1)}

    if not st.session_state.get("survey_1_completed", False):

        # ── Section 1: Experience ────────────────────────────────────
        st.markdown(
            '<span class="section-header">Part A &mdash; Your Experience: </span>'
            'To what extent do you agree or disagree with each statement?',
            unsafe_allow_html=True,
        )

        for i, stmt in enumerate(AGREE_STATEMENTS, 1):
            _render_question(i, stmt, AGREE_OPTIONS, f"Q{i}")

        # ── Section 2: Empathy ───────────────────────────────────────
        st.markdown("---")
        st.markdown(
            '<span class="section-header">Part B &mdash; Empathy with Alex: </span> '
            'How true is each of the following statements for you regarding Alex\'s condition?',
            unsafe_allow_html=True,
        )

        for i, stmt in enumerate(EMPATHY_STATEMENTS, 1):
            _render_question(i + len(AGREE_STATEMENTS), stmt, EMPATHY_OPTIONS, f"Q{i + len(AGREE_STATEMENTS)}")

        # ── Submit ───────────────────────────────────────────────────
        # st.markdown("---")
        if st.button("Next", key="survey_1_submit_button", type="primary"):
            if "Select an option" in st.session_state.survey_response.values():
                st.warning("Please select an option for each question before submitting.")
                return

            survey_data = [
                {"question_id": k, "statement": ALL_STATEMENTS[int(k[1:]) - 1], "response": r}
                for k, r in st.session_state.survey_response.items()
            ]
            save_survey_one(st.session_state.get("prolific_id", "unknown"), survey_data)
            st.session_state.responses_submitted = True
            st.session_state.survey_1_completed = True
            st.rerun()
