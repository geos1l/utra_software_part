# UTRA Match Overlay – Run instructions

## Quick test (React frontend)

1. **Terminal 1 – backend**
   ```bash
   cd c:\Users\silve\utra_hacks\utra_software_part
   pip install -r requirements.txt
   python main.py
   ```
   Leave this running. Backend: http://localhost:8000

2. **Terminal 2 – frontend**
   ```bash
   cd c:\Users\silve\utra_hacks\utra_software_part\frontend
   npm install --legacy-peer-deps
   npm run dev
   ```
   Leave this running. Frontend: http://localhost:3000

3. **Browser:** Open **http://localhost:3000**. Set team number, click Start timer, use test controls. Video stream is at `/stream` (camera must be available for backend).

(If you don’t have a `.env` in the project root yet, copy `.env.example` to `.env` for commentary/TTS; the overlay and React app work without it.)

---

## Option A: React frontend (Next.js)

1. **Backend:** From project root run `python main.py` (backend at http://localhost:8000).
2. **Frontend:** From `frontend/` run `npm install --legacy-peer-deps` then `npm run dev`. Copy `frontend/.env.local.example` to `frontend/.env.local` and set `NEXT_PUBLIC_API_URL=http://localhost:8000`.
3. Open **http://localhost:3000** – the React app talks to the backend API (CORS is enabled for localhost:3000).

## Option B: Static HTML (same origin)

Serve the backend and open http://localhost:8000 for the static HTML overlay.

## What this does

- **Web app**: Live score, timer, "Team x", score breakdown, leaderboard. Team number is set before each match (input + Set team). Timer **does not** start from the browser; it starts when you **press Space** on the machine running the server (keyboard listener in the backend).
- **Stream**: Video from camera (or `VIDEO_SOURCE`) with HUD overlay (Team x, score, timer). Same state as the API; timer runs in the same process as the stream.
- **Commentary**: Optional; run the demo script to test Gemini + ElevenLabs TTS with mock payloads.

## 1. Install dependencies

From `utra_software_part`:

```bash
pip install -r requirements.txt
```

## 2. Configure

The app reads from **`.env`**, not `.env.example`. Copy `.env.example` to `.env` in the project root and set your keys in `.env`:

```bash
copy .env.example .env
```

Then edit `.env` and set:

- `GEMINI_API_KEY` – OpenRouter API key (for commentary).
- `ELEVENLABS_API_KEY` – For TTS (commentary demo).
- `TEAM_NUMBER` – Default team number (e.g. `1`). You can change it per match via the webpage "Set team".
- `VIDEO_SOURCE` – Camera index (e.g. `0` or `2` for DroidCam) or leave `0`.
- `TIMER_START_KEY` – Key to start the timer (default `space`). Only the **backend** (this machine) detects it; the browser does not start the timer.

## 3. Run the web app (overlay + stream)

From `utra_software_part`:

```bash
python main.py
```

Then:

- Open **http://localhost:8000** in a browser (use `localhost` or `127.0.0.1`, not `0.0.0.0`). You’ll see live score, timer, Team x, breakdown, leaderboard, and the video stream with HUD.
- **Start the timer**: Focus the terminal (or this machine) and press **Space**. The timer starts in the backend and updates on the stream and on the webpage (they both read the same state).
- Set **team number** in the "Set team number" section and click "Set team" before each match. Everywhere you’ll see "Team x" where x is that number.
- Use **Test controls** to set obstacle touches, completed under 60s, and box drop to test the score breakdown and leaderboard. Click "Save run to leaderboard" to add the current run.

## 4. Test commentary (Gemini + TTS)

From `utra_software_part` (with `.env` set):

```bash
python run_commentary_demo.py
```

This pushes mock payloads to the commentary runner and runs one Gemini + ElevenLabs TTS call. No CV or web app needed.

## Summary of what was implemented

- **Timer**: Starts only on **key press** (Space by default) on the machine running the server. A background thread in the FastAPI process uses the `keyboard` library to detect the key and call `match_state.set_timer_started()`. The timer is computed in the same process that runs the stream and the API, so the stream HUD and the webpage both show the same elapsed time with no extra hop; the browser only displays data from `/api/state`, it does not start the timer.
- **Team number**: You set it **before each match** via the "Set team number" field and "Set team" button (or via `POST /api/set_team` with `{"team_number": "12"}`). Default comes from `TEAM_NUMBER` in `.env`. Everywhere we show "Team x" (HUD and webpage).
- **Score breakdown**: Obstacle (5 − touches), completed_under_60 (+5), box_drop (fully_in=5, partially_touching=4, mostly_out=1). Test controls let you set these without CV and save runs to the leaderboard.

## Incomplete / follow-up

- **CV integration**: No changes were made to `video.py`, `track.py`, or `test.py`. To drive state from the real CV pipeline, your teammate can call `POST /api/test/set_breakdown` with live values, or you can add a small adapter that reads from their output and updates the state store (or writes to a file that the app reads). The contract is: state lives in `state/store.py`; the API and stream read from it.
- **MongoDB**: Leaderboard is in-memory only. For persistence, add MongoDB (or similar) and replace `state/store.py` leaderboard list with DB reads/writes.
- **Commentary in the loop**: Right now commentary is only tested via `run_commentary_demo.py`. To run commentary during a match, something (e.g. the same process that updates state) must push payloads to `CommentaryRunner.push()` and call `tick()` or run `run_loop()` in a thread; that was not wired into the web app so as not to touch existing files.
