import streamlit as st
from pathlib import Path
from config.settings import API_KEY
from services.gemini_service import init_client, init_chat
from services.db_service import init_db
from ui.sidebar import render_sidebar
from ui.chat_ui import render_chat_ui

# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="Gemini AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    css_path = Path(__file__).parent / "ui" / "style.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def main():
    load_css()

    if not API_KEY:
        st.error("API Key not found! Please set GEMINI_API_KEY in your .env file.")
        return

    # Initialize database tables
    init_db()

    # Initialize Gemini client
    init_client(API_KEY)

    USER_ID = "user_1"

    # Render sidebar with chat history
    render_sidebar(USER_ID)

    # Initialize Gemini chat if a session is active
    if st.session_state.get("active_session_id"):
        init_chat()

    # Render main chat area
    render_chat_ui()


if __name__ == "__main__":
    main()