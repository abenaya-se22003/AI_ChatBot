import os
from dotenv import load_dotenv
from google import genai

# Load .env file and get the API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Create the GenAI Client
client = genai.Client(api_key=api_key)

# Define your System Instruction here
# This tells the AI how to behave (e.g., "You are a helpful Python tutor")
sys_instruct = "You are a helpful AI assistant. Always provide clear, accurate, and professional responses."

print("--- Start the AI Chatbot (Type 'exit' to stop) ---")

try:
    # Start a chat session with System Instructions and History support
    # We pass the instruction inside the config parameter
    chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config={"system_instruction": sys_instruct}
    )

    while True:
        # Get user input from the terminal
        user_input = input("User: ") 
        
        # Stop the loop if the user types 'exit'
        if user_input.lower() == 'exit':
            print("AI Chatbot: Bye Bye!")
            break

        try:
            # Send message within the session to keep history updated
            response = chat_session.send_message(user_input)
            
            print(f"AI Chatbot: {response.text}")
            print("-" * 20)

        except Exception as e:
            print(f"Chat Error : {e}")

except Exception as e:
    # This catches errors during the initial session creation (e.g., API Key issues)
    print(f"Initialization Error : {e}")