"""Post Survey Part 3: demographics (hardcoded)."""

import streamlit as st

from config import PROLIFIC_URL
from firebase_utils import save_survey_three


def close_and_redirect():
    st.link_button("Back to the Prolific and complete the task!", PROLIFIC_URL)


def _update_selected_options():
    st.session_state.selected_options = [
        st.session_state.prior_exp_options[int(k.split("_")[1])]
        for k, v in st.session_state.items()
        if isinstance(v, bool) and v and k.startswith("cbox_")
    ]


def post_survey_three():
    if "survey_2_completed" not in st.session_state:
        st.warning("Please complete the second part of the survey.")
        st.stop()

    submitted = st.session_state.get("survey_submitted", False)

    # Age
    age_options = ["Select your age range", "18-24", "25-34", "35-44", "45-54", "55-64", "65 or above"]
    if "age_range" not in st.session_state:
        st.session_state.age_range = age_options[0]
    age_range = st.selectbox(
        "Please select your age range:",
        options=age_options,
        index=age_options.index(st.session_state.age_range),
        disabled=submitted,
    )
    st.session_state.age_range = age_range

    # Gender
    gender_options = ["Select your gender identity", "Male", "Female", "Non-binary / Third gender", "Prefer not to say"]
    if "gender_identity" not in st.session_state:
        st.session_state.gender_identity = gender_options[0]
    gender = st.selectbox(
        "Please select your gender identity:",
        options=gender_options,
        index=gender_options.index(st.session_state.gender_identity),
        disabled=submitted,
    )
    st.session_state.gender_identity = gender

    # Education
    edu_options = [
        "Select your highest education",
        "Some school, no degree",
        "High school graduate, diploma or the equivalent (e.g. GED)",
        "Some college credit, no degree",
        "Bachelor's degree",
        "Master's degree",
        "Doctorate degree",
        "Prefer not to say",
    ]
    if "highest_education" not in st.session_state:
        st.session_state.highest_education = edu_options[0]
    edu = st.selectbox(
        "What is your highest level of education?",
        options=edu_options,
        index=edu_options.index(st.session_state.highest_education),
        disabled=submitted,
    )
    st.session_state.highest_education = edu

    # Prior experience (multi-select checkboxes)
    prior_options = [
        "I've used an AI chatbot for therapy",
        "I've used an AI chatbot, but never for therapy (this is my first time)",
        "I've been to therapy with a human therapist, but not with an AI chatbot",
        "I've neither used an AI chatbot nor been to therapy",
    ]
    st.session_state.prior_exp_options = prior_options
    st.write("Select your prior experience with AI chatbot or therapy:")
    for i, opt in enumerate(prior_options):
        st.checkbox(opt, key=f"cbox_{i}", on_change=_update_selected_options, disabled=submitted)

    # Submit
    if st.button("Submit", disabled=submitted) and not submitted:
        if age_range == age_options[0]:
            st.error("Please select your age range.")
        elif gender == gender_options[0]:
            st.error("Please select your gender identity.")
        elif edu == edu_options[0]:
            st.error("Please select your highest level of education.")
        elif not st.session_state.get("selected_options"):
            st.error("Please select your prior experience with AI chatbot or therapy.")
        else:
            responses = {
                "age_range": age_range,
                "gender_identity": gender,
                "highest_education": edu,
                "prior_experience": st.session_state.selected_options,
            }
            save_survey_three(st.session_state.prolific_id, responses)
            st.success("Thank you for completing the survey!")
            st.balloons()
            st.session_state.survey_submitted = True
            st.session_state.survey_3_completed = True
            close_and_redirect()
