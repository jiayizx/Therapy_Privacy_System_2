"""Therapy chat helpers: GPT calls, persona CSV loading, streaming."""

import time
import logging

import openai
import pandas as pd
import streamlit as st

from therapy_system.api_key_utils import get_openai_api_key
from config import PERSONA_MODEL


# ── OpenAI helper ────────────────────────────────────────────────────────

def _get_openai_client() -> openai.OpenAI:
    """Return an OpenAI client using the API key from secrets/env."""
    api_key, _ = get_openai_api_key()
    return openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()


def generate_response(
    system_prompt: str,
    user_prompt: str,
    model: str = PERSONA_MODEL,
    max_tokens: int = 8192,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> str | None:
    """Single-shot GPT chat completion. Set json_mode=True for guaranteed JSON output."""
    try:
        kwargs: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = _get_openai_client().chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logging.error("Error in generate_response: %s", e)
        return None


# ── Streaming helper ─────────────────────────────────────────────────────

def stream_data(msg: str):
    msg = msg.strip('"').replace("$", "\\$")
    for word in msg.split(" "):
        yield word + " "
        time.sleep(0.02)


# ── Persona helpers ──────────────────────────────────────────────────────

def gpt4_search_persona(query: str, persona_df: pd.DataFrame) -> str | None:
    """Use GPT to find which persona groups relate to a query."""
    persona_text = persona_df.to_string(index=False).lower()
    system_prompt = f"""
    You are an assistant that helps map queries to relevant persona groups.

    Below is a persona dataset with various groups and their detailed information:

    {persona_text}

    Carefully review the chat history provided. Identify which group names from the dataset are directly and explicitly related to the query.

    Respond in one of these formats only:
    - If there are relevant groups: Only list up to two group names, separated by commas (for example: "Basic information, Recent Relocation").
    - If no group is relevant: Return exactly "None" (without quotes or additional text).

    Do not include explanations or any content other than the group names ("Basic information", "Seeking Help", "Current Medication", "Recent Relocation", "Friendship Crisis", "Therapy History", "Childhood Bullying", "Story with Emily Johnson") or "None".
    """
    user_prompt = f"{query}"
    
    # print(f"Persona info prompt: {system_prompt}")
    response = generate_response(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=PERSONA_MODEL,
        max_tokens=1024,
        temperature=0,
    )
    print(f"Persona info response: {response}")
    return response


def read_persona_csv(filename: str):
    data = pd.read_csv(filename)
    main_categories = data["Group"].unique().tolist()
    category_info = data.groupby("Group")["Detailed information"].apply(list).to_dict()
    return main_categories, category_info, data


def read_unnecessary_info_csv(filename: str):
    data = pd.read_csv(filename, encoding="utf-8")
    return data["unnecessary_info"].tolist(), data.set_index("unnecessary_info").T.to_dict()


# ── Chat reset ───────────────────────────────────────────────────────────

def clean_chat():
    st.session_state.messages = []
    st.session_state.env = None
