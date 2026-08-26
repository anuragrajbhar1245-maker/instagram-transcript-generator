import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Default Whisper Model Configuration
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
DEFAULT_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
DEFAULT_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# Optional Cloud API Keys (for instant sub-second transcription)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# Audio Extraction Settings
AUDIO_CODEC = "mp3"
AUDIO_BITRATE = "128k"
AUDIO_SAMPLE_RATE = 16000  # Optimal for Whisper

# Clerk & JWT & Google Authentication Settings
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "instatranscript-super-secret-production-key-2026")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


