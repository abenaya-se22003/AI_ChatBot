import streamlit as st

def init_messages():
    if "messages" not in st.session_state:
        st.session_state.messages = []