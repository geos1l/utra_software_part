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
from db import mongodb as db_mongodb

# Commentary runner: set in lifespan if Gemini + ElevenLabs keys present
commentary_runner = None

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False


def build_commentary_payload() -> dict:
    """Build one Gemini-shaped payload from current match state (team_id, score_total, t_elapsed_s, score_breakdown, obstacle_touches, match_ended, notable_event)."""
    state = match_state.get_state()
    return {
        "team_id": state.get("team_number", ""),
        "score_total": state.get("score_total", 0),
        "t_elapsed_s": state.get("t_elapsed_s", 0),
        "score_breakdown": state.get("score_breakdown", {}),
        "obstacle_touches": state.get("obstacle_touches", 0),
        "match_ended": state.get("match_ended", False),
        "notable_event": True,
    }


def _timer_key_listener():
    """Backend: TIMER_START_KEY starts match, TIMER_STOP_KEY ends match (debounced)."""
    if not HAS_KEYBOARD:
        return
    start_key = Settings.TIMER_START_KEY
    stop_key = Settings.TIMER_STOP_KEY
    started_pressed = False
    stopped_pressed = False
    while True:
        try:
            if keyboard.is_pressed(start_key):
                if not started_pressed:
                    match_state.set_timer_started()
                    started_pressed = True
                    if commentary_runner is not None:
                        commentary_runner.play_intro()
                    print("[Timer] Started (key press).")
                time.sleep(0.5)
            else:
                started_pressed = False
            if keyboard.is_pressed(stop_key):
                if not stopped_pressed:
                    match_state.set_timer_stopped()
                    stopped_pressed = True
                    print("[Timer] Ended (key press).")
                time.sleep(0.5)
            else:
                stopped_pressed = False
        except Exception:
            pass
        time.sleep(0.05)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global commentary_runner
    match_state.set_team_number(Settings.TEAM_NUMBER)
    if HAS_KEYBOARD:
        t = threading.Thread(target=_timer_key_listener, daemon=True)
        t.start()
    # Start commentary runner if Gemini + ElevenLabs keys are set
    if Settings.GEMINI_API_KEY and Settings.ELEVENLABS_API_KEY:
        try:
            from commentary.commentary_ai import CommentaryAI
            from commentary.commentary_runner import CommentaryRunner
            from commentary.tts import TTSSpeaker
            ai = CommentaryAI(Settings.GEMINI_API_KEY, Settings.GEMINI_MODEL)
            tts = TTSSpeaker(Settings.ELEVENLABS_API_KEY, Settings.ELEVENLABS_VOICE)
            commentary_runner = CommentaryRunner(
                ai, tts,
                filler_interval_sec=Settings.FILLER_INTERVAL_SEC,
                max_payloads_per_call=Settings.MAX_PAYLOADS_PER_CALL,
            )
            threading.Thread(target=commentary_runner.run_loop, kwargs={"poll_interval": 0.5}, daemon=True).start()
            print("[Commentary] Runner started (Gemini + ElevenLabs).")
        except Exception as e:
            print(f"[Commentary] Runner not started: {e}")
            commentary_runner = None
    else:
        commentary_runner = None
    if not Settings.MONGODB_URI:
        print("[MongoDB] MONGODB_URI not set; Save run and leaderboard use in-memory storage.")
    else:
        ok, err = db_mongodb.check_connection()
        if ok:
            print("[MongoDB] Connected and ready.")
        else:
            print(f"[MongoDB] Not connected: {err}; Save run and leaderboard will fail for DB.")
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


@app.get("/api/health/db")
def health_db():
    """Check MongoDB connection. Returns ok=True if connected, ok=False and error message otherwise."""
    if not Settings.MONGODB_URI:
        return {"ok": False, "error": "MONGODB_URI not set", "storage": "in_memory"}
    ok, err = db_mongodb.check_connection()
    if ok:
        return {"ok": True, "storage": "mongodb"}
    return {"ok": False, "error": err or "Connection failed", "storage": "mongodb"}


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
    if commentary_runner is not None:
        commentary_runner.play_intro()
    return match_state.get_state()


@app.post("/api/timer/stop")
def stop_timer():
    """End the match: freeze timer at current value, set match_ended."""
    match_state.set_timer_stopped()
    return match_state.get_state()


@app.post("/api/timer/reset")
def reset_timer():
    """Start new match: clear frozen time and match_ended so timer can start from 0."""
    match_state.reset_for_new_match()
    if commentary_runner is not None:
        commentary_runner.reset_for_new_match()
    return match_state.get_state()


@app.post("/api/set_team")
def set_team(body: SetTeamBody):
    num = body.team_number if body.team_number is not None else body.team
    if num is not None:
        match_state.set_team_number(num)
    return match_state.get_state()


@app.get("/api/leaderboard")
def get_leaderboard():
    if Settings.MONGODB_URI:
        return db_mongodb.get_leaderboard()
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


def _leaderboard_doc_from_state():
    """Build one document for MongoDB from current match state (leaderboard shape)."""
    s = match_state.get_state()
    return {
        "team_number": s["team_number"],
        "team_display": s["team_display"],
        "score_total": s["score_total"],
        "t_elapsed_s": s["t_elapsed_s"],
        "obstacle_touches": s["obstacle_touches"],
        "completed_under_60": s["completed_under_60"],
        "box_drop": s["box_drop"],
        "score_breakdown": s["score_breakdown"],
    }


@app.post("/api/test/save_run")
def save_run():
    if Settings.MONGODB_URI:
        doc = _leaderboard_doc_from_state()
        inserted = db_mongodb.insert_match(doc)
        if inserted is not None:
            saved = {k: v for k, v in inserted.items() if k != "_id"}
            return {"saved": saved, "leaderboard": db_mongodb.get_leaderboard()}
        return {"saved": None, "leaderboard": db_mongodb.get_leaderboard()}
    entry = match_state.save_run_to_leaderboard()
    return {"saved": entry, "leaderboard": match_state.get_leaderboard()}


@app.post("/api/commentary/push")
def commentary_push():
    """Push current match state as one payload to commentary runner (for Gemini + TTS)."""
    payload = build_commentary_payload()
    if commentary_runner is not None:
        commentary_runner.push(payload)
        return {"pushed": True}
    return {"pushed": False}


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
