import streamlit as st
from config.settings import API_KEY
from services.gemini_service import init_client, init_chat
from ui.chat_ui import render_chat_ui

st.set_page_config(page_title="Gemini AI Assistant", layout="centered")

def main():
    if not API_KEY:
        st.error("API Key not found!")
        return

    init_client(API_KEY)
    init_chat()

    render_chat_ui()

if __name__ == "__main__":
    main()