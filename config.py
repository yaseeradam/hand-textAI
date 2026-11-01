import os
import secrets
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # 1. Developer secret API keys
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

        # 2. Client Access Control (Keys you give to others or your own apps)
        self._raw_client_keys: str = os.getenv("ALLOWED_API_KEYS", "*")
        self.ALLOWED_API_KEYS: List[str] = [
            k.strip() for k in self._raw_client_keys.split(",") if k.strip()
        ]

        # 3. Models
        self.DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-flash-lite-latest")
        self.FALLBACK_MODELS: List[str] = ["gemini-flash-latest", "gemini-2.5-flash"]
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

        # 4. Server settings
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.API_TITLE: str = "HandAI OCR & Handwriting Recognition API"
        self.API_VERSION: str = "1.0.0"
        self.API_DESCRIPTION: str = (
            "Enterprise-ready, cross-stack REST API for converting handwritten notes, "
            "whiteboard sketches, and documents into clean, structured Markdown using Google Gemini Vision."
        )

    def is_client_authorized(self, provided_key: str | None) -> bool:
        if "*" in self.ALLOWED_API_KEYS:
            return True
        if not provided_key:
            return False
        return any(secrets.compare_digest(provided_key, key) for key in self.ALLOWED_API_KEYS)

settings = Settings()
