# Quick test – UTRA Match Overlay

Everything is set up. Run these two steps to test.

## 1. Start the backend

In a terminal, from the **project root** (`utra_software_part`):

```bash
cd c:\Users\silve\utra_hacks\utra_software_part
venv\Scripts\activate
python main.py
```

- If you see "Starting server. Open http://localhost:8000...", the backend is running.
- Check it: open **http://localhost:8000/api/health** in a browser; you should see `{"ok": true}`.
- To stop: press **Ctrl+C** once. The server may show "Waiting for connections to close" for up to 2 seconds, then exit. You do not need to press Ctrl+C again.

If port 8000 is already in use, close the other program or change the port in `main.py`.

## 2. Start the React frontend

In a **second** terminal:

```bash
cd c:\Users\silve\utra_hacks\utra_software_part\frontend
npm run dev
```

Leave this running. Frontend: **http://localhost:3000**

## 3. Test in the browser

Open **http://localhost:3000**.

- Set a team number and click **Set team** (you should see "Team X").
- Click **Start timer** (timer should run).
- Use the test controls (Obstacle, Under 60s, Box drop, **Save run**) and check **Breakdown** and **Leaderboard** tabs.

The frontend is already configured to use **http://localhost:8000** via `frontend/.env.local`.
