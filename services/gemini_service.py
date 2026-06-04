import streamlit as st
import time
from google import genai
from config.settings import MODEL_NAME, FALLBACK_MODELS, SYSTEM_INSTRUCTION
from services.rag_service import search_documents, search_documents_with_scores

# Only replay this many recent messages when switching models
MAX_REPLAY_MESSAGES = 10

# Similarity threshold: lower distance = more similar
# Cosine distance < 1.0 means the context is somewhat relevant
RELEVANCE_THRESHOLD = 1.0


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

def _build_hybrid_prompt(prompt):
    """Build a hybrid prompt: always include document context if available,
    and let Gemini decide whether to use it or answer from general knowledge.

    Returns (final_prompt, used_rag) tuple.
    """
    # 🔍 Try to search relevant docs — gracefully handle DB failures
    context = ""
    try:
        docs = search_documents(prompt)
        if docs:
            context = "\n".join(docs)
    except Exception as e:
        # DB down or unreachable — continue without context
        print(f"[Hybrid] DB search failed: {e}")
        context = ""

    if context.strip():
        # ✅ Documents found — provide context + let Gemini decide relevance
        final_prompt = f"""You are a helpful AI assistant. You have access to the following personal knowledge base (CV/resume documents).

=== KNOWLEDGE BASE CONTEXT ===
{context}
=== END CONTEXT ===

User Question: {prompt}

Instructions:
- If the user's question is about a person, their skills, experience, education, or anything that can be answered from the knowledge base context above, answer using that context.
- If the user's question is a general knowledge question (e.g., geography, science, history, programming concepts) that is NOT related to the context above, answer from your own general knowledge. Do NOT say "the context does not contain this information" — just answer the question directly.
- You can combine both sources when appropriate.
- Always be helpful, clear, and professional."""
        return final_prompt, True
    else:
        # ❌ No documents in DB or DB unreachable — pure general knowledge
        final_prompt = f"""You are a helpful AI assistant.

User Question: {prompt}

Please answer this question using your general knowledge. Be clear, accurate, and helpful."""
        return final_prompt, False


def send_message_stream_rag(prompt):
    """Send a message using hybrid RAG + general knowledge and return a stream."""
    final_prompt, used_rag = _build_hybrid_prompt(prompt)
    return send_message_stream(final_prompt)


def send_message_rag(prompt):
    """Send a message using hybrid RAG + general knowledge (non-streaming)."""
    final_prompt, used_rag = _build_hybrid_prompt(prompt)

    # Send to Gemini
    response = st.session_state.chat_session.send_message(
        final_prompt
    )

    return response