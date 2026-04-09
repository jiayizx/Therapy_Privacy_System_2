"""
Centralized OpenAI API key loading. Used across the project.
Priority: 1) Streamlit st.secrets, 2) OPENAI_API_KEY env var.
"""
import os
import logging
from typing import Optional, Tuple


def get_web_login_password() -> Optional[str]:
    """
    Chat gate password from Streamlit ``.streamlit/secrets.toml`` only
    (key ``WEB_LOGIN_PASSWORD``). Returns None if secrets are missing or misconfigured.
    """
    try:
        from streamlit.errors import StreamlitSecretNotFoundError
        import streamlit as st
    except ImportError:
        return None
    try:
        v = st.secrets["WEB_LOGIN_PASSWORD"]
    except StreamlitSecretNotFoundError:
        return None
    except KeyError:
        return None
    if isinstance(v, str) and v.strip():
        return v.strip()
    return None

_SECRETS_KEYS = ("OPENAI_API_KEY", "openai_api_key")


def get_openai_api_key(firestore_db=None) -> Tuple[Optional[str], Optional[str]]:
    """Return (api_key, source) with source in {"st_secrets", "env", None}."""
    # 1. st.secrets (works when running inside Streamlit)
    try:
        import streamlit as st
        for name in _SECRETS_KEYS:
            try:
                key = st.secrets.get(name) if hasattr(st.secrets, "get") else st.secrets[name]
                if key and isinstance(key, str) and key.strip():
                    return (key.strip(), "st_secrets")
            except Exception:
                continue
    except Exception:
        pass

    # 2. Environment variable
    for name in _SECRETS_KEYS:
        key = os.environ.get(name)
        if key and isinstance(key, str) and key.strip():
            return (key.strip(), "env")

    return (None, None)
