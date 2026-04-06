import streamlit as st
from services.gemini_service import send_message, init_chat, new_chat

# 🔹 New Chat Function



def render_chat_ui():
    # Header with button
    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("🤖 Gemini AI Web Assistant")

    with col2:
        if st.button("🆕 New Chat"):
            new_chat()

    # Show history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    prompt = st.chat_input("Type your message...")

    if prompt:
        # Show user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            # Send message to Gemini
            response = send_message(prompt)

            # Show AI response
            with st.chat_message("assistant"):
                st.markdown(response.text)

            # Save response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

        except Exception as e:
            st.error(f"Error: {e}")