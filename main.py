"""Run the UTRA match overlay server (web + stream + timer key listener)."""
import atexit
import signal
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import uvicorn

try:
    import keyboard
except ImportError:
    keyboard = None


def _cleanup_keyboard():
    """Unhook keyboard so Ctrl+C exits cleanly and the terminal stays usable."""
    if keyboard is not None:
        try:
            keyboard.unhook_all()
        except Exception:
            pass


if __name__ == "__main__":
    atexit.register(_cleanup_keyboard)
    # Short graceful shutdown: one Ctrl+C, then exit within 2s (no "waiting for connections" hang)
    # Uvicorn replaces our SIGINT handler when it starts; it handles Ctrl+C and will exit
    # after at most timeout_graceful_shutdown seconds so you don't need to press Ctrl+C twice.
    print("Starting server. Open http://localhost:8000 in your browser (not 0.0.0.0)")
    print("Press Ctrl+C once to stop; server will exit within 2 seconds.")
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        timeout_graceful_shutdown=2,
    )
