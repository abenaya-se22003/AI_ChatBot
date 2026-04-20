import streamlit as st
from services.gemini_service import send_message
from services.db_service import save_message, load_messages, create_session, update_session_title

# 🔹 Demo user (later login system use කරන්න)
USER_ID = "user_1"


def render_chat_ui():
    # 🔹 Ensure there's an active session
    if "active_session_id" not in st.session_state or st.session_state.active_session_id is None:
        # Show welcome screen
        _render_welcome()
        return

    session_id = st.session_state.active_session_id

    # 🔹 Load chat history from DB (only when session changes)
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages(USER_ID, session_id)

    # Header
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <h1 style="font-size: 1.8rem; font-weight: 700; margin: 0;
                    background: linear-gradient(135deg, #6C63FF, #48CFCB);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;">
            🤖 Gemini AI Assistant
        </h1>
    </div>
    """, unsafe_allow_html=True)

    # Show current model
    if "current_model" in st.session_state:
        st.caption(f"📡 Model: `{st.session_state.current_model}`")

    # 🔹 Show message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 🔹 Input
    prompt = st.chat_input("Type your message...")

    if prompt:
        # Show user message
        st.chat_message("user").markdown(prompt)

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # 🔥 Save user message to DB
        save_message(USER_ID, "user", prompt, session_id)

        # 🔹 Auto-title: if this is the first message, use it as the session title
        if len(st.session_state.messages) == 1:
            title = prompt[:50] + ("..." if len(prompt) > 50 else "")
            update_session_title(session_id, title)

        try:
            # Send to Gemini (with automatic fallback)
            with st.spinner("Thinking..."):
                response = send_message(prompt)

            # Show AI response
            with st.chat_message("assistant"):
                st.markdown(response.text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

            # 🔥 Save AI response to DB
            save_message(USER_ID, "assistant", response.text, session_id)

        except Exception as e:
            st.error(f"⚠️ {e}")
            st.info("💡 Tip: Wait 1-2 minutes and try again, or start a new chat.")


def _render_welcome():
    """Show a welcome screen when no chat is active."""
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center;
                justify-content: center; min-height: 60vh; text-align: center;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🤖</div>
        <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0;
                    background: linear-gradient(135deg, #6C63FF, #48CFCB);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;">
            Gemini AI Assistant
        </h1>
        <p style="color: #888; font-size: 1.1rem; margin-top: 0.8rem; max-width: 400px;">
            Start a new conversation by clicking
            <strong style="color:#6C63FF;">➕ New Chat</strong>
            in the sidebar.
        </p>
        <div style="margin-top: 2rem; display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center;">
            <div style="background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.2);
                        border-radius: 12px; padding: 1rem 1.5rem; max-width: 200px;">
                <div style="font-size: 1.5rem;">💡</div>
                <p style="color: #aaa; font-size: 0.85rem; margin: 0.5rem 0 0 0;">Ask me anything about coding, science, or ideas</p>
            </div>
            <div style="background: rgba(72,207,203,0.1); border: 1px solid rgba(72,207,203,0.2);
                        border-radius: 12px; padding: 1rem 1.5rem; max-width: 200px;">
                <div style="font-size: 1.5rem;">📝</div>
                <p style="color: #aaa; font-size: 0.85rem; margin: 0.5rem 0 0 0;">Help with writing, summaries, or translations</p>
            </div>
            <div style="background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.2);
                        border-radius: 12px; padding: 1rem 1.5rem; max-width: 200px;">
                <div style="font-size: 1.5rem;">🔍</div>
                <p style="color: #aaa; font-size: 0.85rem; margin: 0.5rem 0 0 0;">Research topics and get detailed explanations</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)