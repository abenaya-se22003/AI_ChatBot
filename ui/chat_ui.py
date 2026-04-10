import streamlit as st
from google.genai import errors
from services.gemini_service import send_message, new_chat
from services.db_service import save_message, load_messages

# 🔹 Demo user (later login system use කරන්න)
USER_ID = "user_1"


def render_chat_ui():
    # 🔹 Load chat history from DB (only first time)
    if "messages" not in st.session_state:
        st.session_state.messages = load_messages(USER_ID)

    # Header with button
    col1, col2 = st.columns([8, 2])

    with col1:
        st.title("🤖 Gemini AI Web Assistant")

    with col2:
        if st.button("🆕 New Chat"):
            new_chat()
            st.session_state.messages = []   # 🔥 clear UI

    # Show current model info
    if "current_model" in st.session_state:
        st.caption(f"📡 Using model: `{st.session_state.current_model}`")

    # 🔹 Show history
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
        save_message(USER_ID, "user", prompt)

        try:
            # Send to Gemini (with automatic fallback)
            with st.spinner("Thinking... (will try backup models if needed)"):
                response = send_message(prompt)

            # Show AI response
            with st.chat_message("assistant"):
                st.markdown(response.text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

            # 🔥 Save AI response to DB
            save_message(USER_ID, "assistant", response.text)

        except Exception as e:
            st.error(f"⚠️ {e}")
            st.info("💡 Tip: Wait 1-2 minutes and try again, or click '🆕 New Chat' to start fresh.")