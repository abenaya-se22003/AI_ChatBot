import streamlit as st
import time
from google import genai
from google.genai import errors
from config.settings import MODEL_NAME, FALLBACK_MODELS, SYSTEM_INSTRUCTION

def init_client(api_key):
    if "client" not in st.session_state:
        st.session_state.client = genai.Client(api_key=api_key)

def init_chat():
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = st.session_state.client.chats.create(
            model=MODEL_NAME,
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )
    if "current_model" not in st.session_state:
        st.session_state.current_model = MODEL_NAME
    if "messages" not in st.session_state:
        st.session_state.messages = []

def new_chat():
    # Reset chat session and model back to primary
    for key in ["chat_session", "current_model"]:
        if key in st.session_state:
            del st.session_state[key]

    if "messages" in st.session_state:
        st.session_state.messages = []

    st.rerun()

def _try_send(prompt, max_retries=3):
    """Try sending on the current chat session with retries."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return st.session_state.chat_session.send_message(prompt)
        except Exception as e:
            last_error = e
            error_str = str(e)
            # Only retry on 503 errors
            if "503" in error_str or "UNAVAILABLE" in error_str:
                wait_time = 2 * (attempt + 1)  # 2s, 4s, 6s
                print(f"[{st.session_state.current_model}] Retry {attempt+1}/{max_retries}: {e}")
                time.sleep(wait_time)
            else:
                raise  # Non-503 errors should not be retried
    raise last_error

def send_message(prompt):
    """Send message with automatic fallback to alternative models."""

    # Step 1: Try the current model
    try:
        return _try_send(prompt)
    except Exception as primary_error:
        error_str = str(primary_error)
        if "503" not in error_str and "UNAVAILABLE" not in error_str:
            raise  # Not a capacity issue, re-raise immediately

        print(f"⚠️ Primary model '{st.session_state.current_model}' is unavailable. Trying fallbacks...")

    # Step 2: Try each fallback model
    for fallback_model in FALLBACK_MODELS:
        if fallback_model == st.session_state.current_model:
            continue  # Skip if it's the same as what we already tried

        try:
            print(f"🔄 Switching to fallback model: {fallback_model}")

            # Create a new chat session with the fallback model
            st.session_state.chat_session = st.session_state.client.chats.create(
                model=fallback_model,
                config={"system_instruction": SYSTEM_INSTRUCTION}
            )
            st.session_state.current_model = fallback_model

            # Replay previous messages to maintain context
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.session_state.chat_session.send_message(msg["content"])

            # Now send the actual new message
            response = st.session_state.chat_session.send_message(prompt)
            print(f"✅ Successfully using fallback model: {fallback_model}")
            return response

        except Exception as fallback_error:
            error_str = str(fallback_error)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                print(f"❌ Fallback model '{fallback_model}' also unavailable.")
                continue
            else:
                raise  # Non-503 error on fallback

    # Step 3: All models failed
    raise Exception(
        "All AI models are currently experiencing high demand. "
        "Please wait a few minutes and try again."
    )