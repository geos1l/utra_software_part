"""FastAPI app: state API, stream+HUD, timer key listener (backend starts timer on key press)."""
import sys
import time
import threading
import cv2
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.settings import Settings
from state.store import match_state

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


def _timer_key_listener():
    """Backend: when TIMER_START_KEY is pressed, start timer (debounced)."""
    if not HAS_KEYBOARD:
        return
    key = Settings.TIMER_START_KEY
    started = False
    while True:
        try:
            if keyboard.is_pressed(key):
                if not started:
                    match_state.set_timer_started()
                    started = True
                    print("[Timer] Started (key press).")
                time.sleep(0.5)
            else:
                started = False
        except Exception:
            pass
        time.sleep(0.05)


@asynccontextmanager
async def lifespan(app: FastAPI):
    match_state.set_team_number(Settings.TEAM_NUMBER)
    if HAS_KEYBOARD:
        t = threading.Thread(target=_timer_key_listener, daemon=True)
        t.start()
    yield
    # Unhook keyboard on shutdown so the process and terminal exit cleanly
    if HAS_KEYBOARD:
        try:
            keyboard.unhook_all()
        except Exception:
            pass


app = FastAPI(title="UTRA Match Overlay", lifespan=lifespan)

# CORS so the React/Next frontend (e.g. localhost:3000) can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Simple health check so you can verify the backend is running."""
    return {"ok": True}


@app.get("/api/state")
def get_state():
    return match_state.get_state()


class SetTeamBody(BaseModel):
    team_number: str | int | None = None
    team: str | int | None = None  # frontend may send "team" instead of "team_number"


@app.post("/api/timer/start")
def start_timer():
    """Start the match timer (call from page or key press)."""
    match_state.set_timer_started()
    return match_state.get_state()


@app.post("/api/set_team")
def set_team(body: SetTeamBody):
    num = body.team_number if body.team_number is not None else body.team
    if num is not None:
        match_state.set_team_number(num)
    return match_state.get_state()


@app.get("/api/leaderboard")
def get_leaderboard():
    return match_state.get_leaderboard()


class SetBreakdownBody(BaseModel):
    obstacle_touches: int | None = None
    completed_under_60: bool | None = None
    box_drop: str | None = None  # "fully_in" | "partially_touching" | "mostly_out"


@app.post("/api/test/set_breakdown")
def set_breakdown(body: SetBreakdownBody):
    match_state.set_breakdown(
        obstacle_touches=body.obstacle_touches,
        completed_under_60=body.completed_under_60,
        box_drop=body.box_drop,
    )
    return match_state.get_state()


@app.post("/api/test/save_run")
def save_run():
    entry = match_state.save_run_to_leaderboard()
    return {"saved": entry, "leaderboard": match_state.get_leaderboard()}


def _stream_generator():
    """Read camera, draw HUD (Team x, score, timer), yield MJPEG."""
    cap = None
    try:
        cap = cv2.VideoCapture(Settings.VIDEO_SOURCE)
        if not cap.isOpened():
            yield b""
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            state = match_state.get_state()
            t_elapsed = state["t_elapsed_s"]
            m = int(t_elapsed // 60)
            s = int(t_elapsed % 60)
            time_str = f"{m:02d}:{s:02d}"
            team_display = state["team_display"]
            score = state["score_total"]
            # Draw HUD
            cv2.putText(
                frame, f"{team_display}", (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2
            )
            cv2.putText(
                frame, f"Score: {score}", (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
            )
            cv2.putText(
                frame, f"Time: {time_str}", (10, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2
            )
            _, jpeg = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")
    except Exception as e:
        print(f"[Stream] Error: {e}")
    finally:
        if cap is not None:
            cap.release()


@app.get("/stream")
def stream():
    return StreamingResponse(
        _stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# Serve static HTML from web/static
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _read_static_html(name: str) -> str:
    path = Path(__file__).resolve().parent / "static" / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<h1>Not found</h1>"


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=_read_static_html("index.html"))


@app.get("/breakdown", response_class=HTMLResponse)
def breakdown_page():
    return HTMLResponse(content=_read_static_html("breakdown.html"))


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page():
    return HTMLResponse(content=_read_static_html("leaderboard.html"))
