"""Post Survey Part 2: GPT-detected PII feedback (generated from chat)."""

import threading
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from survey_utils import (
    read_posthoc_survey_info_csv,
    set_user_conversation,
    get_survey_info,
    get_user_selections,
)
from config import POSTHOC_CSV


def prep_survey_two():
    """Pre-load conversation data and kick off PII detection in a background thread."""
    if "user_conversation" not in st.session_state:
        set_user_conversation()

    if "posthoc_survey_info" not in st.session_state:
        st.session_state.posthoc_survey_info = read_posthoc_survey_info_csv(POSTHOC_CSV)

    if "complete_detections" not in st.session_state:
        thread_name = "complete_detections_thread"
        if not any(t.name == thread_name for t in threading.enumerate()):
            t = threading.Thread(
                target=lambda: get_survey_info(),
                name=thread_name,
            )
            add_script_run_ctx(t)
            t.start()

    st.session_state.prep_done = True


def post_survey_two():
    """Main entry for survey part 2."""
    if "prolific_id" not in st.session_state or not st.session_state.prolific_id:
        st.warning("Please go back to the main page and enter your Prolific ID.")
        st.stop()

    if "survey_1_completed" not in st.session_state:
        st.warning("Please complete the first part of the survey.")
        st.stop()

    if "posthoc_survey_info" not in st.session_state:
        st.session_state.posthoc_survey_info = read_posthoc_survey_info_csv(POSTHOC_CSV)

    get_user_selections()
