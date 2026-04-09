"""Survey orchestrator page: runs parts 1 -> 2 -> 3 in sequence."""

import streamlit as st

from post_survey_1 import post_survey_one
from post_survey_2 import post_survey_two, prep_survey_two
from post_survey_3 import post_survey_three, close_and_redirect


def main():
    st.title("Survey")

    if "prolific_id" not in st.session_state or not st.session_state.prolific_id:
        st.warning("Please go back to the 'Chat with AI Therapist' page and enter your Prolific ID.")
        st.stop()

    if st.session_state.get("phase") != "post_survey":
        st.warning("Please complete the chat session before proceeding to the survey.")
        st.stop()

    if not st.session_state.get("prep_done", False):
        prep_survey_two()

    if "survey_1_completed" not in st.session_state:
        post_survey_one()
    elif "survey_2_completed" not in st.session_state:
        post_survey_two()
    elif "survey_3_completed" not in st.session_state:
        post_survey_three()
    else:
        st.write("You have already completed the survey.")
        close_and_redirect()


if __name__ == "__main__":
    main()
