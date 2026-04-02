import os
from dotenv import load_dotenv
from google import genai


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


client = genai.Client(api_key=api_key)

try:
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents="what is genarative AI?"
    )
    
    print("AI Chatbot:", response.text)

except Exception as e:
    print(f"Error : {e}")