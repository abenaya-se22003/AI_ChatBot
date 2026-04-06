import streamlit as st
from services.gemini_service import send_message

def render_chat_ui():
    st.title("🤖 Gemini AI Web Assistant")

    # Show history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    prompt = st.chat_input("Type your message...")

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            response = send_message(prompt)

            with st.chat_message("assistant"):
                st.markdown(response.text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

        except Exception as e:
            st.error(f"Error: {e}")