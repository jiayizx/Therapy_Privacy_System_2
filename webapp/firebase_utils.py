"""Centralized Firebase Firestore setup and all save operations."""

import json
import logging
import time

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_firebase():
    """Initialise Firebase from st.secrets or env. Sets st.session_state.firestore_db."""
    firebase_creds = None
    for key in ("firebase_service_account", "FIREBASE_SERVICE_ACCOUNT"):
        try:
            firebase_creds = st.secrets[key]
            break
        except Exception:
            continue

    if firebase_creds is None:
        import os
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if raw:
            firebase_creds = json.loads(raw) if isinstance(raw, str) else raw

    if not firebase_creds:
        logging.info("Firebase credentials not found – running in local mode.")
        st.session_state.firestore_db = None
        return

    if not isinstance(firebase_creds, dict):
        firebase_creds = dict(firebase_creds)

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
        logging.info("Firebase initialised.")

    st.session_state.firestore_db = firestore.client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db():
    db = st.session_state.get("firestore_db")
    if db is None:
        logging.info("Firestore not configured (local mode) – skipping save.")
    return db


def _save(collection: str, prefix: str, prolific_id: str, data: dict):
    db = _get_db()
    if db is None:
        return
    doc_name = f"{prefix}_{prolific_id}_{int(time.time())}"
    doc = {"prolific_id": prolific_id, **data, "timestamp": firestore.SERVER_TIMESTAMP}
    try:
        db.collection(collection).document(doc_name).set(doc)
        logging.info("Saved to %s/%s", collection, doc_name)
    except Exception as e:
        logging.error("Failed to save to %s: %s", collection, e)


# ---------------------------------------------------------------------------
# Public save functions
# ---------------------------------------------------------------------------

def save_chat_history(prolific_id: str, chat_history):
    _save("group_two_chat_histories_2026", "chat", prolific_id, {"chat_history": chat_history})


def save_survey_one(prolific_id: str, survey_data):
    _save("group_two_survey_one_responses_2026", "survey_one", prolific_id, {"survey_data": survey_data})


def save_survey_two(prolific_id: str, feedback: dict):
    _save("group_two_survey_two_responses_2026", "survey_two", prolific_id, feedback)


def save_survey_three(prolific_id: str, responses: dict):
    _save("group_two_survey_three_responses_2026", "survey_three", prolific_id, {"survey_data": responses})
