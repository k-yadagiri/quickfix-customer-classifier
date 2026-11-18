"""Settings, read from environment variables (and an optional .env file)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str) -> str:
    """Return the env var, or the default if it is missing or empty."""
    value = os.getenv(name, "").strip()
    return value if value else default


LLM_BASE_URL = _env("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
LLM_MODEL = _env("LLM_MODEL", "qwen2.5:3b")
LLM_API_KEY = _env("LLM_API_KEY", "ollama")  # Ollama accepts any text
LLM_TIMEOUT_SECONDS = float(_env("LLM_TIMEOUT_SECONDS", "120"))
DB_PATH = _env("DB_PATH", str(BASE_DIR / "quickfix.db"))
