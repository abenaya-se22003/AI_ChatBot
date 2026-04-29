import streamlit as st
from services.gemini_service import send_message_stream
from services.db_service import save_message, load_messages, update_session_title

USER_ID = "user_1"


def render_chat_ui():
    if not st.session_state.get("active_session_id"):
        _render_welcome()
        return

    session_id = st.session_state.active_session_id

    # Load chat history from DB
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages(USER_ID, session_id)

    st.markdown("## 🤖 Gemini AI Assistant")

    if "current_model" in st.session_state:
        st.caption(f"📡 Model: `{st.session_state.current_model}`")

    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Type your message...")

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_message(USER_ID, "user", prompt, session_id)

        # Auto-title on first message
        if len(st.session_state.messages) == 1:
            title = prompt[:50] + ("..." if len(prompt) > 50 else "")
            update_session_title(session_id, title)

        try:
            with st.chat_message("assistant"):
                def generate_stream():
                    for chunk in send_message_stream(prompt):
                        if chunk.text:
                            yield chunk.text

                full_response = st.write_stream(generate_stream())

            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_message(USER_ID, "assistant", full_response, session_id)

        except Exception as e:
            st.error(f"⚠️ {e}")
            st.info("💡 Wait 1-2 minutes and try again, or start a new chat.")


def _render_welcome():
    """Welcome screen when no chat is active."""
    st.markdown("")
    st.markdown("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🤖 Gemini AI Assistant")
        st.markdown("Start a new conversation by clicking **➕ New Chat** in the sidebar.")
        st.markdown("")
        c1, c2, c3 = st.columns(3)
        c1.info("💡 Ask me anything about coding, science, or ideas")
        c2.info("📝 Help with writing, summaries, or translations")
        c3.info("🔍 Research topics and get detailed explanations")