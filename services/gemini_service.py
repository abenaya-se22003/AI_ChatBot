import streamlit as st
from google import genai
from config.settings import MODEL_NAME, SYSTEM_INSTRUCTION

def init_client(api_key):
    if "client" not in st.session_state:
        st.session_state.client = genai.Client(api_key=api_key)

def init_chat():
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = st.session_state.client.chats.create(
            model=MODEL_NAME,
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []

def new_chat():
    if "chat_session" in st.session_state:
        del st.session_state.chat_session

    if "messages" in st.session_state:
        st.session_state.messages = []

    st.rerun()

def send_message(prompt):
    return st.session_state.chat_session.send_message(prompt)