import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-1.5-pro")

    response = model.generate_content("What is the capital of Sri Lanka?")
    print(response.text)
    