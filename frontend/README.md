# UTRA Match Overlay – Frontend (Next.js + React Native Web)

React/Next.js app for the UTRA match overlay. Connects to the Python FastAPI backend for state, timer, score breakdown, and leaderboard.

## Setup

1. **Install dependencies**

   ```bash
   cd frontend
   npm install --legacy-peer-deps
   ```
   (Use `--legacy-peer-deps` if you see a peer dependency conflict with react-native-web and React 19.)

2. **Configure API URL**

   Copy `.env.local.example` to `.env.local` and set the backend URL:

   ```bash
   copy .env.local.example .env.local
   ```

   Edit `.env.local` and set:

   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

   (Use the URL where the backend is running.)

## Run

1. **Start the backend** (from project root):

   ```bash
   cd ..
   python main.py
   ```

   Backend runs at http://localhost:8000.

2. **Start the frontend** (from `frontend`):

   ```bash
   npm run dev
   ```

   Frontend runs at http://localhost:3000 and will call the backend at the URL in `NEXT_PUBLIC_API_URL`.

3. Open **http://localhost:3000** in your browser. The app will poll the backend for state, timer, and leaderboard.

## Project layout

- `app/` – Next.js App Router (layout, page)
- `components/rn/` – Match overlay views (live, score breakdown, leaderboard, navigation)
- `lib/api.ts` – API client; maps backend (snake_case) to frontend (camelCase)
- `lib/types.ts` – Shared types and colors
