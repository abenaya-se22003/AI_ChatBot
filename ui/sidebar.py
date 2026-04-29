import streamlit as st
from services.db_service import get_sessions, create_session, delete_session, load_messages


def _reset_chat_state():
    """Clear Gemini chat session keys so a fresh one is created."""
    for key in ["chat_session", "current_model"]:
        st.session_state.pop(key, None)


def render_sidebar(user_id):
    with st.sidebar:
        st.markdown("## 🤖 Gemini AI")

        if st.button("➕  New Chat", key="new_chat_btn", use_container_width=True):
            new_id = create_session(user_id, "New Chat")
            if new_id:
                st.session_state.active_session_id = new_id
                st.session_state.messages = []
                _reset_chat_state()
                st.rerun()

        st.markdown("---")
        st.caption("💬 CHAT HISTORY")

        sessions = get_sessions(user_id)

        if not sessions:
            st.caption("No chats yet. Start a new conversation!")
        else:
            for session in sessions:
                _render_session_item(session, user_id)


def _render_session_item(session, user_id):
    session_id = session["id"]
    title = session["title"]
    date_str = session["created_at"].strftime("%b %d") if session["created_at"] else ""
    is_active = st.session_state.get("active_session_id") == session_id

    col1, col2 = st.columns([5, 1])

    with col1:
        label = f"▸ {title}" if is_active else f"  {title}"
        if st.button(label, key=f"session_{session_id}", use_container_width=True, help=f"Created: {date_str}"):
            st.session_state.active_session_id = session_id
            st.session_state.messages = load_messages(user_id, session_id)
            _reset_chat_state()
            st.rerun()

    with col2:
        if st.button("🗑️", key=f"del_{session_id}", help="Delete this chat"):
            delete_session(session_id)
            if st.session_state.get("active_session_id") == session_id:
                st.session_state.active_session_id = None
                st.session_state.messages = []
                _reset_chat_state()
            st.rerun()
