import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_INSTRUCTION = "You are a helpful AI assistant. Provide clear and professional responses."

# Primary model and fallbacks (tried in order)
MODEL_NAME = "gemini-2.5-flash"
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]