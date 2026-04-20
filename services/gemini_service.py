import streamlit as st
import time
from google import genai
from google.genai import errors
from config.settings import MODEL_NAME, FALLBACK_MODELS, SYSTEM_INSTRUCTION


def _is_switchable_error(error_str):
    """Returns True if the error means we should switch models (not retry same one)."""
    return any(code in error_str for code in [
        "503", "UNAVAILABLE",         # server overloaded
        "429", "RESOURCE_EXHAUSTED",  # quota exceeded
        "404", "NOT_FOUND",           # model not available in this API version
    ])


def _is_retryable_error(error_str):
    """Returns True if a short wait + retry on SAME model might help (only 503)."""
    return "503" in error_str or "UNAVAILABLE" in error_str


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
    for key in ["chat_session", "current_model"]:
        if key in st.session_state:
            del st.session_state[key]

    if "messages" in st.session_state:
        st.session_state.messages = []

    st.rerun()


def _try_send_with_retry(prompt, max_retries=2):
    """Try sending on the current session. Retry only for 503 (not 429)."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return st.session_state.chat_session.send_message(prompt)
        except Exception as e:
            last_error = e
            error_str = str(e)
            if _is_retryable_error(error_str):
                wait_time = 2 * (attempt + 1)
                print(f"[{st.session_state.current_model}] Retry {attempt + 1}/{max_retries} in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                # 429, auth errors, etc — don't retry same model
                raise
    raise last_error


def _switch_to_model(model_name):
    """Create a new chat session for the given model, replaying history."""
    st.session_state.chat_session = st.session_state.client.chats.create(
        model=model_name,
        config={"system_instruction": SYSTEM_INSTRUCTION}
    )
    st.session_state.current_model = model_name

    # Replay existing conversation so context is preserved
    history = st.session_state.get("messages", [])
    for msg in history:
        if msg["role"] == "user":
            try:
                st.session_state.chat_session.send_message(msg["content"])
            except Exception:
                pass  # Best-effort context replay


def send_message(prompt):
    """Send a message with automatic model fallback on 429 or 503."""
    all_models = [MODEL_NAME] + [m for m in FALLBACK_MODELS if m != MODEL_NAME]

    # Make sure we start from the current active model
    if "current_model" in st.session_state:
        current = st.session_state.current_model
        # Move current model to front if it's a fallback
        if current in all_models:
            all_models = [current] + [m for m in all_models if m != current]

    last_error = None
    for model in all_models:
        # Switch to this model if it's not already active
        if st.session_state.get("current_model") != model:
            print(f"🔄 Switching to model: {model}")
            try:
                _switch_to_model(model)
            except Exception as e:
                print(f"Failed to switch to {model}: {e}")
                last_error = e
                continue

        # Try sending
        try:
            response = _try_send_with_retry(prompt)
            print(f"✅ Response from: {st.session_state.current_model}")
            return response
        except Exception as e:
            last_error = e
            error_str = str(e)
            if _is_switchable_error(error_str):
                print(f"❌ Model '{model}' failed ({error_str[:60]}...). Trying next...")
                continue
            else:
                # Hard error (auth, invalid request, etc) — don't try other models
                raise

    # All models exhausted
    raise Exception(
        "All available AI models have hit their quota or are unavailable.\n\n"
        "Free tier limits: 20 requests/day per model.\n"
        "Please wait until tomorrow, or upgrade your Google AI plan."
    )