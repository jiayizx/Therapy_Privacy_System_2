import os
import sys
import time
import logging
import types

import streamlit as st

# Repo root first — otherwise a same-named `therapy_system` on sys.path (e.g. site-packages)
# can shadow this project and break imports like `get_web_login_password`.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import therapy_system
from therapy_system.utils import unescape_special_characters
from therapy_system.action.therapy import (
    build_therapist_system_prompt,
    build_therapist_system_prompt_persuasive,
    TAXONOMY,
)
from therapy_system.api_key_utils import get_openai_api_key, get_web_login_password

from config import (
    AGENT_MODEL, MIN_TURNS, MAX_TURNS, MIN_INTERACTION_TIME,
    WORDS_LIMIT, PERSONA_CSV, UNN_INFO_CSV, disable_copy_paste,
)
from firebase_utils import setup_firebase, save_chat_history
from post_survey_2 import prep_survey_two
from therapy_utils import (
    stream_data, generate_response, gpt4_search_persona,
    read_persona_csv, read_unnecessary_info_csv,
)

logging.basicConfig(level=logging.INFO)

# ── Streamlit page config ────────────────────────────────────────────────

st.set_page_config(
    initial_sidebar_state="expanded",
    page_title="Chat with AI Therapist",
    layout="wide",
)

# ── Session-state defaults ───────────────────────────────────────────────

_DEFAULTS = {
    "phase": "initial",
    "messages": [],
    "start_time": None,
    "chat_finished": False,
    "current_iteration": 0,
    "turn": 0,
    "temp_response": "",
    "prolific_id": None,
    "prolific_id_entered": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Load API key into env (once) ────────────────────────────────────────

if "api_key_loaded" not in st.session_state:
    api_key, source = get_openai_api_key()
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        logging.info("OpenAI API key loaded from %s", source)
    else:
        st.warning("OpenAI API key not found. Set it in .streamlit/secrets.toml or export OPENAI_API_KEY.")
    st.session_state.api_key_loaded = True

# ── Firebase (once) ─────────────────────────────────────────────────────

if "firestore_db" not in st.session_state:
    setup_firebase()

# ── Persona data (once) ─────────────────────────────────────────────────

if "persona_data" not in st.session_state:
    main_cats, cat_info, hierarchy_df = read_persona_csv(PERSONA_CSV)
    read_unnecessary_info_csv(UNN_INFO_CSV)
    st.session_state.persona_data = {
        "main_categories": main_cats,
        "category_info": cat_info,
        "hierarchy_df": hierarchy_df,
    }

_persona = st.session_state.persona_data


# ═══════════════════════════════════════════════════════════════════════════
# Phase 1 – Login
# ═══════════════════════════════════════════════════════════════════════════

def show_login():
    st.header("Role-play as Alex and Chat with the AI therapist")
    prolific_id = st.text_input("Your Prolific ID")
    password = st.text_input("Chat Password", type="password")

    if st.button("Enter"):
        expected = get_web_login_password()
        if expected is None:
            st.error(
                "Missing `WEB_LOGIN_PASSWORD` in Streamlit secrets. Copy `webapp/.streamlit/secrets.example.toml` "
                "to `webapp/.streamlit/secrets.toml`, set `WEB_LOGIN_PASSWORD`, then restart the app."
            )
        elif not prolific_id:
            st.warning("Please enter a valid Prolific ID to continue.")
        elif password != expected:
            st.warning("Please enter a valid password to continue.")
        else:
            st.session_state.prolific_id = prolific_id
            st.session_state.prolific_id_entered = True
            st.session_state.phase = "chat"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Phase 2 – Chat
# ═══════════════════════════════════════════════════════════════════════════

PERSUASION_FLAG = True # use the persuasion techniques
IS_STREAM = True
PLAYERS = ["assistant", "user"]


def _build_system_prompt():
    if PERSUASION_FLAG:
        return build_therapist_system_prompt_persuasive(techniques=TAXONOMY, words_limit=WORDS_LIMIT)
    return build_therapist_system_prompt(words_limit=WORDS_LIMIT)


def init_conversation():
    """Create the therapy environment and reset chat state."""
    agent_details = {
        "name": "assistant",
        "engine": AGENT_MODEL,
        "system": _build_system_prompt(),
        "action_space": {"name": "therapy", "action": -1},
        "model_args": {"stream": IS_STREAM},
        "role": "assistant",
        "prolific_id": st.session_state.prolific_id,
    }
    human_details = {
        "engine": "Human",
        "system": "",
        "action_space": {"name": "human"},
        "role": "user",
        "name": "user",
    }
    env = therapy_system.make(
        "Therapy",
        agents=[agent_details, human_details],
        init_message=None,
        transit=["assistant", "user"] * MAX_TURNS,
        persuasion_flag=PERSUASION_FLAG,
        words_limit=WORDS_LIMIT,
    )
    st.session_state.update(
        messages=[],
        env=env,
        current_iteration=0,
        start_time=time.time(),
        iterations=MIN_TURNS,
        max_iterations=MAX_TURNS,
        turn=0,
        temp_response="",
        conversation_initialized=True,
    )


def display_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["turn"]):
            st.write(msg["response"])


# ── Sidebar persona helpers ──────────────────────────────────────────────

def display_persona_info():
    """Show the static persona info in the sidebar."""
    if "sidebar_container" not in st.session_state:
        st.session_state.sidebar_container = st.sidebar.container()
    with st.session_state.sidebar_container:
        st.markdown("#### Personal Information")
        for cat in _persona["main_categories"]:
            if cat != "Seeking Help":
                with st.expander(cat):
                    for info in _persona["category_info"][cat]:
                        st.write(info)


def retrieve_persona_details(formatted_query):
    """Use GPT to find related persona groups and display them in the sidebar."""
    detected_groups = gpt4_search_persona(formatted_query, _persona["hierarchy_df"])

    st.session_state.sidebar_container = st.sidebar.container()

    with st.session_state.sidebar_container:
        st.markdown("#### Possible Related Information")
        if detected_groups and detected_groups != "None":
            cat_map = {c.lower(): c for c in _persona["category_info"]}
            for group in detected_groups.split(", "):
                proper = cat_map.get(group.lower().strip())
                if proper and proper in _persona["category_info"]:
                    st.markdown(f"**{proper}**:")
                    for item in _persona["category_info"][proper]:
                        st.markdown(f"- {item}")
        else:
            # sys_prompt = (
            #     f'Here is the recent chat history: "{formatted_query}"\n'
            #     "You can intelligently complement the persona information. "
            #     "First understand what this query is about, then generate simple "
            #     "and concrete persona information.\n"
            #     "Return only the response content without any prefixes or labels."
            # )
            # gen = generate_response(sys_prompt, "Generate relevant persona information", max_tokens=100, temperature=0)
            # st.write("No relevant persona information found. Here is the **newly generated persona information**: ", gen)
            st.write("No relevant persona information found.")
        display_persona_info()


# ── Conversation turn logic ──────────────────────────────────────────────

def _handle_human_input(form_key: str, input_key: str):
    """Display a text-input form for the human player. Returns True if submitted."""
    with st.form(key=form_key, clear_on_submit=True):
        response = st.text_input("You:", key=input_key)
        submitted = st.form_submit_button(label="Send")
    if submitted and response:
        with st.chat_message("user"):
            st.write(response)
        st.session_state.temp_response = response
        st.session_state.messages.append({"turn": "user", "response": response})
        st.rerun()
    return False


def _finish_chat():
    """Save chat, start survey-2 detection in background, then transition to survey."""
    st.session_state.chat_finished = True
    st.session_state.phase = "post_survey"
    env = st.session_state.env
    save_chat_history(st.session_state.prolific_id, env.log_state())
    prep_survey_two()
    st.switch_page("pages/Survey.py")


def run_conversation():
    """Execute one iteration of the conversation loop."""
    env = st.session_state.env
    cur = st.session_state.current_iteration
    max_iter = st.session_state.max_iterations
    min_iter = st.session_state.iterations
    elapsed = time.time() - st.session_state.start_time
    past_min = cur >= min_iter
    past_max = cur >= max_iter

    # ── Max reached: mandatory survey ────────────────────────────────
    if past_max:
        st.info("You have reached the maximum number of turns.")
        if st.button("Proceed to Survey", key=f"proceed_survey_{cur}"):
            _finish_chat()
        st.stop()

    # ── Sample the next action ───────────────────────────────────────
    action = env.sample_action()
    technique = None
    is_human = str(action) == "Human-input"

    # Show "End Therapy" only once, right before the human input form
    if is_human and st.session_state.temp_response == "":
        if past_min:
            if st.button("End Therapy (Feel free to end anytime)", key="end_therapy"):
                _finish_chat()
        _handle_human_input(f"human_form_{cur}", f"human_input_{cur}")
        st.stop()

    if is_human:
        response = st.session_state.temp_response
    else:
        technique, response = env.get_response(action)
        with st.chat_message("assistant"):
            if IS_STREAM and isinstance(response, types.GeneratorType):
                placeholder = st.empty()
                full = ""
                for chunk in response:
                    full += chunk
                    placeholder.markdown(unescape_special_characters(full) + "▌")
                placeholder.markdown(unescape_special_characters(full))
                response = full
                if isinstance(technique, list):
                    technique = technique[0]
            elif IS_STREAM:
                response = unescape_special_characters(response)
                placeholder = st.empty()
                full = ""
                for chunk in stream_data(response):
                    full += chunk
                    placeholder.markdown(full + "▌")
                placeholder.markdown(full)
                response = full
            else:
                st.write(unescape_special_characters(response))
        st.session_state.messages.append({"turn": "assistant", "response": response})

    response = unescape_special_characters(response)

    # Update persona sidebar after human input
    if is_human and len(st.session_state.messages) > 1:
        prev = st.session_state.messages[-2]["response"]
        retrieve_persona_details(f"Therapist: {prev}\nPatient: {response}")
    if "sidebar_container" not in st.session_state:
        display_persona_info()

    _, _, _, _, _ = env.step(action, technique, response)
    st.session_state.turn += 1
    st.session_state.temp_response = ""
    st.session_state.current_iteration += 1


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if st.session_state.phase == "initial":
        show_login()

    elif st.session_state.phase in ("chat", "post_survey"):
        disable_copy_paste()

        header = st.container()
        header.image("webapp/assets/instruction.png", use_container_width=True)
        c1, c2 = header.columns(2)
        c1.image("webapp/assets/UserBioWeb1.png", use_container_width=True)
        c2.image("webapp/assets/UserBioWeb2.png", use_container_width=True)

        st.sidebar.title("Your Related Information")

        if "conversation_initialized" not in st.session_state:
            init_conversation()

        if st.session_state.env is not None:
            display_messages()

            if st.session_state.phase == "chat":
                while True:
                    run_conversation()
                    if st.session_state.chat_finished:
                        break

        if st.session_state.phase == "post_survey":
            if st.button("Proceed to Survey"):
                st.switch_page("pages/Survey.py")


if __name__ == "__main__":
    main()
