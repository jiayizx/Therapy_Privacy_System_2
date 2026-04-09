"""Survey 2 logic: GPT-based PII detection, user selection UI, and reasoning collection."""

import re
import os
import json
import logging
from collections import defaultdict
from typing import List

import pandas as pd
import streamlit as st

from config import DETECTION_MODEL, POSTHOC_CSV, MIN_REASONING_WORDS, disable_copy_paste
from firebase_utils import save_survey_two
from therapy_utils import generate_response


# ── Conversation extraction ──────────────────────────────────────────────

def set_user_conversation():
    """Extract chat history into separate lists and a full dialogue string."""
    msgs = st.session_state.get("messages", [])
    st.session_state.usr_conv_list = [m["response"] for m in msgs if m["turn"] == "user"]
    st.session_state.agt_conv_list = [m["response"] for m in msgs if m["turn"] == "assistant"]
    # Full dialogue with speaker labels for better detection context
    turns = []
    for m in msgs:
        speaker = "Therapist" if m["turn"] == "assistant" else "Patient"
        turns.append(f"{speaker}: {m['response']}")
    st.session_state.user_conversation = "\n".join(turns)


# ── CSV loader ───────────────────────────────────────────────────────────

def read_posthoc_survey_info_csv(filename: str = POSTHOC_CSV) -> pd.DataFrame:
    return pd.read_csv(filename, encoding="utf-8")


# ── GPT PII detection ───────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a precise semantic analyzer. You will receive a therapy dialogue where \
a patient (role-playing as "Alex") talks to an AI therapist, plus a numbered \
list of personal-information phrases.

For each phrase, determine whether the PATIENT revealed that information \
(explicitly, by paraphrase, or by clear logical inference) during the conversation. \
Only count information disclosed by the Patient, not the Therapist.

Respond with a single JSON object. Each key is the phrase index (as a string), \
and each value is an object with:
  - "present": "Yes" or "No"
  - "evidence": the exact Patient quote(s) that reveal the information \
    (separate multiple quotes with " | "). Omit this field when "present" is "No".

Rules:
- "Yes" only when the information is explicitly stated, clearly paraphrased, \
  or logically inferrable from what the Patient said.
- "No" when it requires speculation or is only mentioned by the Therapist.
- Evidence must be verbatim quotes from the Patient's turns only.\
"""


def _build_numbered_phrases(phrases: list[str]) -> str:
    return "\n".join(f"  {i}: {p}" for i, p in enumerate(phrases))


def get_survey_info() -> dict:
    """Use GPT to detect which PII phrases appear in the user conversation."""
    phrases = st.session_state.posthoc_survey_info["user_mentioned"].tolist()
    dialogue = st.session_state.user_conversation

    user_prompt = f"""\
### Phrases to check (index: phrase):
{_build_numbered_phrases(phrases)}

### Dialogue:
{dialogue}

Return ONLY the JSON object described in your instructions. No extra text.\
"""

    raw = generate_response(
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=DETECTION_MODEL,
        max_tokens=4096,
        temperature=0,
        json_mode=True,
    )

    logging.info("Detection GPT response: %s", raw)

    if not raw or not isinstance(raw, str):
        logging.warning("LLM returned no response for PII classification.")
        st.session_state.complete_detections = {}
        return {}

    try:
        llm_responses = json.loads(raw)
    except json.JSONDecodeError as e:
        logging.error("Failed to parse LLM response as JSON: %s", e)
        st.session_state.complete_detections = {}
        return {}

    info_df = st.session_state.posthoc_survey_info
    questions: dict = {}
    for key, val in llm_responses.items():
        if val.get("present", "").lower() == "yes":
            idx = int(key)
            questions[key] = {
                "revealation": val["evidence"],
                "category": info_df.loc[idx, "category"],
                "priority": str(int(info_df.loc[idx, "category priority"])),
                "user_mentioned": info_df.loc[idx, "user_mentioned"],
                "survey_display": info_df.loc[idx, "survey_display"],
            }
    st.session_state.complete_detections = questions
    return questions


# ── Evidence enhancement ─────────────────────────────────────────────────

def _enhance_evidence(evidence: str, usr_list: List[str], agt_list: List[str]) -> str:
    for i, msg in enumerate(usr_list):
        if evidence in msg:
            return f"AI therapy:{agt_list[i]} {os.linesep} You: **{evidence}**"
    return f"You: **{evidence}**"


# ── Survey sampling ──────────────────────────────────────────────────────

def get_survey_sample(all_detections: dict, max_display: int = 10) -> dict:
    """Round-robin sample detections across categories (up to max_display)."""
    usr = st.session_state.usr_conv_list
    agt = st.session_state.agt_conv_list
    for det in all_detections.values():
        det["better_evidence"] = _enhance_evidence(det["revealation"], usr, agt)

    if len(all_detections) <= max_display:
        return all_detections

    categories: dict[str, list] = defaultdict(list)
    for key, val in all_detections.items():
        categories[val["category"]].append(key)

    sampled: dict = {}
    while len(sampled) < max_display:
        for cat in sorted(categories):
            if len(sampled) >= max_display:
                break
            if categories[cat]:
                k = categories[cat].pop(0)
                sampled[k] = all_detections[k]
    return sampled


# ── Session-state setup ──────────────────────────────────────────────────

def _init_survey_state():
    defaults = {
        "disable_user_selections": False,
        "disable_necessary_reasons": True,
        "disable_unnecessary_reasons": True,
        "disable_submit": True,
        "user_selections_fixed": False,
        "user_nec_reasons_entered": False,
        "user_unnec_reasons_entered": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "user_selections" not in st.session_state:
        st.session_state.user_selections = set()
        st.session_state.user_non_selections = set()


# ── Reasoning validation ─────────────────────────────────────────────────

_WS = re.compile(r"\s{2,}")


def _validate_reasoning(keys: set, suffix: str, var_name: str):
    """Check that every reasoning text area has enough words. Only inspects known keys."""
    for k in keys:
        val = st.session_state.get(f"reasoning_{k}_{suffix}", "")
        cleaned = _WS.sub(" ", val).strip()
        if not cleaned or len(cleaned.split()) < MIN_REASONING_WORDS:
            st.session_state[var_name] = True
            return
    st.session_state[var_name] = False


# ── Fix selections callback ─────────────────────────────────────────────

def _fix_user_selections():
    st.session_state.disable_user_selections = True
    survey_info = st.session_state.survey_info
    for k in survey_info:
        if st.session_state.get(f"checkbox_{k}", False):
            st.session_state.user_selections.add(k)
        else:
            st.session_state.user_non_selections.add(k)
    st.session_state.user_selections_fixed = True


# ── Capture reasoning callbacks ──────────────────────────────────────────

def _capture_reasoning(suffix: str, selected: bool, flag: str):
    survey_info = st.session_state.survey_info
    keys = st.session_state.user_selections if suffix == "necessary" else st.session_state.user_non_selections
    for k in keys:
        val = st.session_state.get(f"reasoning_{k}_{suffix}", "")
        survey_info[k]["reasoning"] = val
        survey_info[k]["selected"] = selected
    st.session_state[flag] = True


def _save_and_advance():
    """Store feedback in Firebase and mark survey 2 as complete."""
    feedback = {
        "user_conversation": st.session_state.get("user_conversation", ""),
        "messages": st.session_state.get("messages", []),
        "complete_detections": st.session_state.get("complete_detections", {}),
        "user_selections": list(st.session_state.get("user_selections", [])),
        "survey_info": st.session_state.get("survey_info", {}),
    }
    prolific_id = st.session_state.get("prolific_id", "unknown")
    save_survey_two(prolific_id, feedback)

    st.session_state.survey_2_completed = True
    st.session_state.user_selections_fixed = True
    st.session_state.user_nec_reasons_entered = True
    st.session_state.user_unnec_reasons_entered = True
    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Main public entry point
# ═══════════════════════════════════════════════════════════════════════════

def get_user_selections():
    """Full survey-2 UI: PII detection -> selection -> necessary/unnecessary reasoning."""
    if "user_conversation" not in st.session_state:
        set_user_conversation()

    if "complete_detections" not in st.session_state:
        with st.spinner("Analyzing conversation..."):
            st.session_state.complete_detections = get_survey_info()

    if "survey_info" not in st.session_state:
        st.session_state.survey_info = get_survey_sample(st.session_state.complete_detections)

    survey_info = st.session_state.survey_info
    _init_survey_state()
    disable_copy_paste()

    # ── Step 1: selection checkboxes ─────────────────────────────────
    if not st.session_state.user_selections_fixed:
        if not survey_info:
            st.info("No personally identifiable information was detected in your conversation. Proceeding to the next section.")
            _save_and_advance()
            return

        st.subheader("Select the following information that you think it's necessary to share for the therapy")
        for key, val in survey_info.items():
            st.checkbox(val["survey_display"], key=f"checkbox_{key}", value=False)
        st.button("Next", on_click=_fix_user_selections)
        return

    # ── Step 2: necessary reasoning ──────────────────────────────────
    if not st.session_state.user_nec_reasons_entered:
        if st.session_state.user_selections:
            st.subheader("Why you think following information is :blue[necessary] to share for the therapy session?")
            for key in st.session_state.user_selections:
                c1, c2 = st.columns(2)
                c1.write(survey_info[key]["survey_display"])
                with c1.expander("See in chat"):
                    st.write(f":grey[{survey_info[key]['better_evidence']}]")
                c2.text_area("_", key=f"reasoning_{key}_necessary", label_visibility="collapsed", height=120)

            _validate_reasoning(st.session_state.user_selections, "necessary", "disable_necessary_reasons")
            st.button(
                "Next",
                on_click=lambda: _capture_reasoning("necessary", True, "user_nec_reasons_entered"),
                disabled=st.session_state.disable_necessary_reasons,
                help=f"Provide reasoning for all with at-least {MIN_REASONING_WORDS} words to proceed.",
                key="next_nec",
            )
            return

        # No necessary items to explain -- skip to next step
        _capture_reasoning("necessary", True, "user_nec_reasons_entered")
        st.rerun()

    # ── Step 3: unnecessary reasoning ────────────────────────────────
    if not st.session_state.user_unnec_reasons_entered:
        if st.session_state.user_non_selections:
            st.header("Why you think following information is :blue[unnecessary] to share for the therapy session, but you still share that with the chatbot?")
            for key in st.session_state.user_non_selections:
                c1, c2 = st.columns(2)
                c1.write(survey_info[key]["survey_display"])
                with c1.expander("See in chat"):
                    st.write(f":grey[{survey_info[key]['better_evidence']}]")
                c2.text_area("_", key=f"reasoning_{key}_unnecessary", label_visibility="collapsed")

            _validate_reasoning(st.session_state.user_non_selections, "unnecessary", "disable_unnecessary_reasons")
            st.button(
                "Next",
                on_click=lambda: _capture_reasoning("unnecessary", False, "user_unnec_reasons_entered"),
                disabled=st.session_state.disable_unnecessary_reasons,
                help=f"Provide reasoning for all with at-least {MIN_REASONING_WORDS} words to proceed.",
                key="next_unnec",
            )
            return

        # No unnecessary items to explain -- skip to save
        _capture_reasoning("unnecessary", False, "user_unnec_reasons_entered")

    # ── All steps done → save & advance ──────────────────────────────
    with st.spinner("Saving responses..."):
        _save_and_advance()
