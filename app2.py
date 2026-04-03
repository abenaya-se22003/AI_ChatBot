import os
from dotenv import load_dotenv
from google import genai

# Load .env file and get the API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Create the GenAI Client
client = genai.Client(api_key=api_key)

print("--- Start the AI Chatbot (Type 'exit' to stop) ---")

# Start a chat session to maintain history
# Using gemini-2.5-flash as the model
chat_session = client.chats.create(model="gemini-2.5-flash")

while True:
    # Get user input from the terminal
    user_input = input("User: ") 
    
    # Stop the loop if the user types 'exit'
    if user_input.lower() == 'exit':
        print("AI Chatbot: Bye Bye!")
        break

    try:
        # Use send_message instead of generate_content to keep history updated
        response = chat_session.send_message(user_input)
        
        print(f"AI Chatbot: {response.text}")
        print("-" * 20)

    except Exception as e:
        # Display error message if something goes wrong
        print(f"Error : {e}")