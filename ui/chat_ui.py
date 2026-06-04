import streamlit as st

# 🔥 Use RAG response function
from services.gemini_service import send_message_stream_rag

from services.db_service import (
    save_message,
    load_messages,
    update_session_title
)

USER_ID = "user_1"


def render_chat_ui():

    # 🔹 No active chat
    if not st.session_state.get("active_session_id"):
        _render_welcome()
        return

    session_id = st.session_state.active_session_id

    # 🔹 Load chat history
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages(
            USER_ID,
            session_id
        )

    # 🔹 Header
    st.markdown("## 🤖 Gemini AI Assistant")

    # 🔹 Current model
    if "current_model" in st.session_state:
        st.caption(
            f"📡 Model: `{st.session_state.current_model}`"
        )

    # 🔹 Show previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 🔹 Chat input
    prompt = st.chat_input("Ask about the CV or any general question...")

    if prompt:

        # ==========================================
        # USER MESSAGE
        # ==========================================

        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Save user message
        save_message(
            USER_ID,
            "user",
            prompt,
            session_id
        )

        # ==========================================
        # AUTO CHAT TITLE
        # ==========================================

        if len(st.session_state.messages) == 1:

            title = (
                prompt[:50] + "..."
                if len(prompt) > 50
                else prompt
            )

            update_session_title(
                session_id,
                title
            )

        # ==========================================
        # AI RESPONSE (RAG)
        # ==========================================

        try:

            with st.chat_message("assistant"):

                # 🔥 Streaming generator
                def generate_stream():

                    # 🔥 RAG STREAM
                    for chunk in send_message_stream_rag(prompt):

                        if chunk.text:
                            yield chunk.text

                # 🔥 Stream to UI
                full_response = st.write_stream(
                    generate_stream
                )

            # ==========================================
            # SAVE AI MESSAGE
            # ==========================================

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

            save_message(
                USER_ID,
                "assistant",
                full_response,
                session_id
            )

        except Exception as e:

            st.error(f"⚠️ {e}")

            st.info(
                "💡 AI temporarily unavailable. "
                "Please wait a bit or start a new chat."
            )


# =====================================================
# WELCOME SCREEN
# =====================================================

def _render_welcome():

    st.markdown("")
    st.markdown("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.markdown("# 🤖 Gemini AI Assistant")

        st.markdown(
            """
            This chatbot supports **Hybrid AI**:

            ✅ **CV/Document Questions** → Answers from your uploaded documents  
            ✅ **General Knowledge** → Answers from Gemini AI  
            ✅ **Smart Routing** → Automatically detects which source to use  
            ✅ **Chat History** → Previous conversations saved  
            """
        )

        st.markdown("")

        c1, c2, c3 = st.columns(3)

        c1.info(
            "📄 Ask about skills, experience from your CV"
        )

        c2.info(
            "🌍 Ask general questions like capitals, facts"
        )

        c3.info(
            "🧠 AI smartly picks the best source to answer"
        )