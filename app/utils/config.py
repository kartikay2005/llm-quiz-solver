"""Configuration management with environment variables."""
import os
from dataclasses import dataclass

# Only load .env file if not in serverless environment
if not os.getenv("VERCEL"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available in serverless


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    SECRET: str = os.getenv("QUIZ_SECRET", "changeme")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # AIPipe configuration (institution LLM API)
    AIPIPE_API_URL: str = os.getenv("AIPIPE_API_URL", "https://aipipe.org/openrouter/v1/chat/completions")
    AIPIPE_MODEL: str = os.getenv("AIPIPE_MODEL", "openai/gpt-4o")
    USE_AIPIPE: bool = os.getenv("USE_AIPIPE", "1") in ("1", "true", "True")
    
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "1") in ("1", "true", "True")
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", ".downloads")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_WINDOW_SECONDS: int = int(os.getenv("RETRY_WINDOW_SECONDS", "180"))


settings = Settings()
