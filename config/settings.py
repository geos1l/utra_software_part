"""Centralized configuration from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (not .env.example — copy that to .env and add your keys)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")


class Settings:
    """Application settings for UTRA commentary and web pipeline."""

    # Gemini via OpenRouter (live commentary)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "google/gemini-2.5-flash-lite")

    # ElevenLabs TTS (mirrors Hackhive Project 2026)
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE = os.getenv("ELEVENLABS_VOICE", "josh")

    # Timer: key press to start/end (detected in backend when running)
    TIMER_START_KEY = os.getenv("TIMER_START_KEY", "space")
    TIMER_STOP_KEY = os.getenv("TIMER_STOP_KEY", "escape")

    # Team number: set before each match (default from env; can override via API)
    TEAM_NUMBER = os.getenv("TEAM_NUMBER", "1")

    # Video source: camera index (0, 1, 2...) or URL for stream
    VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")
    try:
        VIDEO_SOURCE = int(VIDEO_SOURCE)
    except ValueError:
        pass  # keep as string for URL

    # Commentary rate limiting
    FILLER_INTERVAL_SEC = float(os.getenv("FILLER_INTERVAL_SEC", "12.0"))
    MAX_PAYLOADS_PER_CALL = int(os.getenv("MAX_PAYLOADS_PER_CALL", "3"))

    # Paths
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    OUTPUT_DIR = PROJECT_ROOT / "output"

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing required env vars (for commentary/TTS)."""
        required = ["ELEVENLABS_API_KEY", "GEMINI_API_KEY"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            env_path = _root / ".env"
            print(
                "\n  The app reads from .env, not .env.example.\n"
                f"  Copy .env.example to .env in the project root and add your keys to .env:\n"
                f"    {env_path}\n"
                f"  Missing: {', '.join(missing)}\n"
            )
        return missing
