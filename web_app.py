import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

# 1. Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 2. Configure Streamlit Page
st.set_page_config(page_title="Gemini AI Web Assistant", layout="centered")
st.title("🤖 Gemini AI Web Assistant")

# 3. Initialize Client in Session State (This fixes the "Client closed" error)
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=api_key)

# 4. Define System Instruction
sys_instruct = "You are a helpful AI assistant. Provide clear and professional responses."

# 5. Initialize Chat Session in Session State
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.client.chats.create(
        model="gemini-2.5-flash", 
        config={"system_instruction": sys_instruct}
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# 6. Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Handle User Input
if prompt := st.chat_input("Type your message here..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        # Use the client from session_state
        response = st.session_state.chat_session.send_message(prompt)
        
        with st.chat_message("assistant"):
            st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error occurred: {e}")
        # If the client fails, you might need to refresh the page