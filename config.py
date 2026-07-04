import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database/chatbot.db")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

settings = Settings()

print(f"[CONFIG] NVIDIA_API_KEY loaded: '{settings.NVIDIA_API_KEY[:8]}...' len={len(settings.NVIDIA_API_KEY)}")