import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:  # python-dotenv is optional at runtime
    pass

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "screener.db"
STATIC_DIR = BASE_DIR / "static"          # built React app is served from here

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_MB = 10

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
PORT = int(os.getenv("PORT", "5000"))

# Scoring weights (must add up to 1.0)
W_SKILLS = 0.55
W_TEXT = 0.35
W_QUALITY = 0.10
