# UTRA Match Overlay

Live overlay and scoring system for a timed robot obstacle-course run. Single robot runs the track; the app shows team, score, timer, score breakdown, and optional AI commentary (Gemini + ElevenLabs TTS). Leaderboard can be stored in memory or MongoDB Atlas.

## Features

- **Live match view** – Team number, score, timer (start / end / reset via buttons)
- **Score breakdown** – Obstacle touches (5 − touches at match end), under-60s bonus (+5), up to two box drops per match (5/4/2/1 pts per rubric)
- **AI commentary** – Gemini + ElevenLabs TTS (via OpenRouter); reacts to touches, box drops, and match end; rapid events are coalesced into one comment
- **Leaderboard** – Save runs; view sorted by score. Persists to MongoDB Atlas if configured, otherwise in-memory
- **Video stream** – Camera feed with HUD overlay (team, score, timer) at `/stream`
- **Two UIs** – Next.js React app or static HTML pages served by the backend

## Project structure

```
utra_software_part/
├── main.py              # Run server (uvicorn)
├── web/
│   ├── app.py           # FastAPI app: state API, timer, breakdown, leaderboard, stream, commentary push
│   └── static/          # Static HTML (index, breakdown, leaderboard)
├── frontend/             # Next.js + React Native Web
│   ├── app/             # App Router (layout, page)
│   ├── components/rn/   # Live match, score breakdown, leaderboard views
│   └── lib/             # API client, types
├── state/
│   └── store.py         # Match state (timer, score, box drops, leaderboard)
├── commentary/
│   ├── commentary_ai.py # Gemini (OpenRouter) commentary
│   ├── commentary_runner.py  # Queue, coalesce, TTS
│   └── tts.py           # ElevenLabs TTS
├── config/
│   └── settings.py      # Env-based settings
├── db/
│   └── mongodb.py       # MongoDB Atlas (optional) for leaderboard
├── .env.example         # Copy to .env and fill in keys
└── requirements.txt
```

## Prerequisites

- **Python 3.11+**
- **Node.js** (for React frontend)
- **OpenRouter** API key (Gemini), **OpenRouter** API key (ElevenLabs), **MongoDB Atlas** URI (leaderboard persistence)

## Setup

### 1. Backend

From the project root:

```powershell
pip install -r requirements.txt
```

Copy env and edit (commentary/TTS/DB are optional; overlay works without them):

```powershell
Copy-Item .env.example .env
```

Important variables in `.env`:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | OpenRouter API key (commentary development) |
| `GEMINI_MODEL` | e.g. `google/gemini-3-flash-preview` |
| `ELEVENLABS_API_KEY` | OpenRouter API key (TTS) |
| `ELEVENLABS_VOICE` | e.g. `josh` |
| `TEAM_NUMBER` | Default team (e.g. `1`) |
| `VIDEO_SOURCE` | Camera index (`0`, `1`, …) or URL |
| `MONGODB_URI` | Optional; if set, leaderboard persists to Atlas |
| `MONGODB_DB_NAME` | DB name (e.g. `utra_match`) |
| `MONGODB_COLLECTION` | Collection (e.g. `matches`) |

### 2. Frontend (Next.js, optional)

From `frontend/`:

```powershell
cd frontend
npm install --legacy-peer-deps
```

Copy env and set backend URL:

```powershell
Copy-Item .env.local.example .env.local
```

In `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Run

### Option A: React frontend (recommended)

1. **Start backend** (project root):

   ```powershell
   python main.py
   ```

   Backend: **http://localhost:8000**

2. **Start frontend** (separate terminal, from `frontend/`):

   ```powershell
   npm run dev
   ```

   Frontend: **http://localhost:3000**

3. Open **http://localhost:3000**. Use Live tab for timer and score controls; set team number, then Start / End / Reset match. Use test controls for obstacle touches and box drops; save runs to the leaderboard. Leaderboard and Score breakdown tabs show saved data.

### Option B: Static HTML (same origin)

1. Start only the backend:

   ```powershell
   python main.py
   ```

2. Open **http://localhost:8000** for the main overlay. Use **http://localhost:8000/breakdown** and **http://localhost:8000/leaderboard** for breakdown and leaderboard.

## Scoring

- **Obstacles** – Each touch subtracts 1 during the match; at match end we add 5 once (net: 5 − touches; 0 touches ⇒ +5, 5 touches ⇒ 0).
- **Under 60s** – +5 only if match has ended and “Completed under 60s” is set.
- **Box drops** – Up to two per match. Each rated: 5 = fully in, 4 = edge touching, 2 = less than half out, 1 = mostly out. Total box points = sum of the two.

## API (summary)

- `GET /api/state` – Current match state (team, score, timer, breakdown, box_drop_1/2).
- `POST /api/timer/start` – Start match timer.
- `POST /api/timer/end` – End match (freeze time, set match_ended).
- `POST /api/timer/reset` – New match (clear timer and scoring).
- `POST /api/test/set_breakdown` – Set obstacle_touches, completed_under_60, box_drop_1, box_drop_2.
- `POST /api/commentary/push` – Push current state to commentary queue (called by frontend on breakdown/timer actions).
- `GET /api/leaderboard` – Leaderboard entries (from memory or MongoDB).
- `POST /api/test/save_run` – Save current run to leaderboard.
- `GET /stream` – MJPEG video stream with HUD (if camera available).

## Commentary

If `GEMINI_API_KEY` and `ELEVENLABS_API_KEY` are set, the backend starts a commentary runner: it buffers payloads from `POST /api/commentary/push`, coalesces rapid events into the latest state, and sends that to Gemini; the reply is spoken via ElevenLabs. A neutral intro plays when the timer starts; after match end, a wrap-up is spoken and commentary stops until the next match (timer reset).

## MongoDB (optional)

To persist the leaderboard, set `MONGODB_URI` (and optionally `MONGODB_DB_NAME`, `MONGODB_COLLECTION`) in `.env`. Use the format:

```
MONGODB_URI=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
```

`GET /api/health/db` returns connection status. See project docs (e.g. `MONGODB.md` if present) for setup details.

## License

See repository.
