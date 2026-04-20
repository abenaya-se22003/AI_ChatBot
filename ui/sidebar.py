import streamlit as st
from services.db_service import get_sessions, create_session, delete_session


def render_sidebar(user_id):
    """Render the sidebar with chat history."""

    with st.sidebar:
        # ── App branding ──
        st.markdown("""
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <span style="font-size: 1.8rem;">🤖</span>
            <h2 style="margin:0; font-size:1.3rem; font-weight:700;
                        background: linear-gradient(135deg, #6C63FF, #48CFCB);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;">
                Gemini AI
            </h2>
        </div>
        """, unsafe_allow_html=True)

        # ── New Chat button ──
        if st.button("➕  New Chat", key="new_chat_btn", use_container_width=True):
            # Create a new session in DB
            new_id = create_session(user_id, "New Chat")
            if new_id:
                st.session_state.active_session_id = new_id
                st.session_state.messages = []
                # Reset the Gemini chat session so a fresh one is created
                if "chat_session" in st.session_state:
                    del st.session_state.chat_session
                if "current_model" in st.session_state:
                    del st.session_state.current_model
                st.rerun()

        st.markdown("---")

        # ── Chat history list ──
        st.markdown(
            "<p style='font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; "
            "color:#888; margin-bottom:0.5rem; font-weight:600;'>💬 Chat History</p>",
            unsafe_allow_html=True
        )

        sessions = get_sessions(user_id)

        if not sessions:
            st.markdown(
                "<p style='color:#666; font-size:0.85rem; padding:1rem 0; text-align:center;'>"
                "No chats yet.<br>Start a new conversation!</p>",
                unsafe_allow_html=True
            )
        else:
            for session in sessions:
                _render_session_item(session, user_id)


def _render_session_item(session, user_id):
    """Render a single chat session item in the sidebar."""
    session_id = session["id"]
    title = session["title"]
    created = session["created_at"]
    is_active = st.session_state.get("active_session_id") == session_id

    # Format date
    date_str = created.strftime("%b %d") if created else ""

    col1, col2 = st.columns([5, 1])

    with col1:
        # Use a different style for active session
        if is_active:
            btn_label = f"▸ {title}"
        else:
            btn_label = f"  {title}"

        if st.button(
            btn_label,
            key=f"session_{session_id}",
            use_container_width=True,
            help=f"Created: {date_str}"
        ):
            _switch_session(session_id, user_id)

    with col2:
        if st.button("🗑️", key=f"del_{session_id}", help="Delete this chat"):
            _delete_session(session_id, user_id)


def _switch_session(session_id, user_id):
    """Switch to a different chat session."""
    from services.db_service import load_messages

    st.session_state.active_session_id = session_id
    st.session_state.messages = load_messages(user_id, session_id)

    # Reset Gemini chat session so it gets re-created
    if "chat_session" in st.session_state:
        del st.session_state.chat_session
    if "current_model" in st.session_state:
        del st.session_state.current_model

    st.rerun()


def _delete_session(session_id, user_id):
    """Delete a chat session."""
    delete_session(session_id)

    # If we deleted the active session, switch to another
    if st.session_state.get("active_session_id") == session_id:
        st.session_state.active_session_id = None
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state.chat_session
        if "current_model" in st.session_state:
            del st.session_state.current_model

    st.rerun()
