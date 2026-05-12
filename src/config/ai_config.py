import os
from dotenv import load_dotenv

load_dotenv()

class AIConfig:
    MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-3.1-flash-live-preview")
    API_KEY = os.getenv("GEMINI_API_KEY")
    TIMEOUT = int(os.getenv("AI_TIMEOUT", 20))
    RETRY_LIMIT = int(os.getenv("AI_RETRY_LIMIT", 2))
    TEMPERATURE = float(os.getenv("AI_TEMPERATURE", 0.1))
    MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", 1000))
