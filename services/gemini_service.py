import streamlit as st
import time
from google import genai
from config.settings import MODEL_NAME, FALLBACK_MODELS, SYSTEM_INSTRUCTION
from services.rag_service import search_documents

# Only replay this many recent messages when switching models
MAX_REPLAY_MESSAGES = 10


def _is_switchable_error(error_str):
    """Check if we should try a different model (503, 429, 404)."""
    return any(code in error_str for code in [
        "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND",
    ])


def _is_retryable_error(error_str):
    """Check if retrying the same model might help (only 503)."""
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


def _try_send_stream(prompt, max_retries=2):
    """Try sending with retry on 503 errors."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return st.session_state.chat_session.send_message_stream(prompt)
        except Exception as e:
            last_error = e
            if _is_retryable_error(str(e)):
                time.sleep(0.5)
            else:
                raise
    raise last_error


def _switch_to_model(model_name):
    """Create a new chat session on a different model, replaying recent history."""
    st.session_state.chat_session = st.session_state.client.chats.create(
        model=model_name,
        config={"system_instruction": SYSTEM_INSTRUCTION}
    )
    st.session_state.current_model = model_name

    # Only replay the last N messages to keep the switch fast
    recent = st.session_state.get("messages", [])[-MAX_REPLAY_MESSAGES:]
    for msg in recent:
        if msg["role"] == "user":
            try:
                st.session_state.chat_session.send_message(msg["content"])
            except Exception:
                pass


def send_message_stream(prompt):
    """Send a message and return a stream, with automatic model fallback."""
    current = st.session_state.get("current_model", MODEL_NAME)
    # Build ordered model list: current model first, then remaining fallbacks
    all_models = [current] + [
        m for m in [MODEL_NAME] + FALLBACK_MODELS if m != current
    ]

    last_error = None
    for model in all_models:
        if st.session_state.get("current_model") != model:
            try:
                _switch_to_model(model)
            except Exception as e:
                last_error = e
                continue

        try:
            return _try_send_stream(prompt)
        except Exception as e:
            last_error = e
            if _is_switchable_error(str(e)):
                continue
            raise

    raise Exception(
        "All AI models are unavailable or quota exhausted.\n"
        "Please wait and try again, or upgrade your Google AI plan."
    )

def send_message_stream_rag(prompt):
    """Send a message using RAG context and return a stream, with automatic model fallback."""
    # 🔍 Search relevant docs
    docs = search_documents(prompt)

    # Combine context
    context = "\n".join(docs)

    # Final AI prompt
    final_prompt = f"""
    Answer using the context below.

    Context:
    {context}

    User Question:
    {prompt}
    """

    return send_message_stream(final_prompt)


def send_message_rag(prompt):

    # 🔍 Search relevant docs
    docs = search_documents(prompt)

    # Combine context
    context = "\n".join(docs)

    # Final AI prompt
    final_prompt = f"""
    Answer using the context below.

    Context:
    {context}

    User Question:
    {prompt}
    """

    # Send to Gemini
    response = st.session_state.chat_session.send_message(
        final_prompt
    )

    return response