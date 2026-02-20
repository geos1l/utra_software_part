# MongoDB setup and connection checks

This project can store saved runs in **MongoDB Atlas** (or any MongoDB server). If `MONGODB_URI` is not set, the leaderboard uses **in-memory storage** only (data is lost when you restart the backend).

---

## 1. Set your MongoDB connection string

1. **Get a connection string** from [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (or your MongoDB host):
   - Log in → your cluster → **Connect** → **Drivers** (or **Connect your application**).
   - Copy the URI. It looks like:  
     `mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

2. **Put it in `.env`** (in the project root, same folder as `main.py`):

   - Open `.env` and add **one line** with your URI. **Yes, just paste the full URI** you copied from Atlas. No quotes.
   ```env
   MONGODB_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=utra_match
   MONGODB_COLLECTION=matches
   ```
  
   - If you copied the URI from Atlas, it already has your username and a placeholder for the password. Replace `<password>` in that URI with your **actual database user password** (the one you set in Atlas under **Database Access**).
   - Do **not** wrap the value in quotes. One line, no spaces around `=`.
   - `MONGODB_DB_NAME` and `MONGODB_COLLECTION` are optional; defaults are `utra_match` and `matches`.

3. **Restart the backend** so it reads the new `.env` (e.g. stop and run `python main.py` or `uvicorn web.app:app` again).

---

## 2. Check MongoDB at startup (console)

When you start the backend:

- **If `MONGODB_URI` is not set**  
  You should see:
  ```text
  [MongoDB] MONGODB_URI not set; Save run and leaderboard use in-memory storage.
  ```
  → Leaderboard is in-memory only. No MongoDB checks run.

- **If `MONGODB_URI` is set and connection succeeds**  
  You should see:
  ```text
  [MongoDB] Connected and ready.
  ```
  → Save run and leaderboard use MongoDB.

- **If `MONGODB_URI` is set but connection fails**  
  You should see something like:
  ```text
  [MongoDB] Connection failed: <error message>
  [MongoDB] Not connected: <error message>; Save run and leaderboard will fail for DB.
  ```
  → Fix the error (see section 5) and restart.

**What to do:** Start the app, then look at the terminal for one of the three messages above.

---

## 3. Check MongoDB via the API (any time)

You can test the MongoDB connection **without restarting** by calling the health endpoint.

### Option A: Browser

1. Make sure the backend is running (e.g. `python main.py` or `uvicorn web.app:app`).
2. Open in your browser:
   ```text
   http://localhost:8000/api/health/db
   ```
3. You’ll get JSON. Interpret it like this:

   | Response | Meaning |
   |----------|--------|
   | `{"ok": true, "storage": "mongodb"}` | MongoDB is connected and used for leaderboard. |
   | `{"ok": false, "error": "MONGODB_URI not set", "storage": "in_memory"}` | No URI in `.env`; leaderboard is in-memory only. |
   | `{"ok": false, "error": "<some message>", "storage": "mongodb"}` | URI is set but connection failed; see `error` and section 5. |

### Option B: Command line (curl)

```bash
curl http://localhost:8000/api/health/db
```

Same JSON as above; use the table to interpret it.

### Option C: PowerShell (Windows)

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health/db"
```

Again, same JSON and same interpretation.

---

## 4. Quick checklist

- [ ] `.env` exists in the project root (same folder as `main.py`).
- [ ] `.env` contains `MONGODB_URI=...` with your real connection string (no quotes needed).
- [ ] Backend was restarted after changing `.env`.
- [ ] Startup log shows either `[MongoDB] Connected and ready.` or the “not set” / “Not connected” message.
- [ ] `GET http://localhost:8000/api/health/db` returns `"ok": true` when you expect MongoDB to be used.

---

## 5. If connection fails

- **"MONGODB_URI not set"**  
  Add `MONGODB_URI=...` to `.env` and restart the backend.

- **"bad auth : authentication failed" / "Authentication failed"**  
  Atlas is rejecting the username or password in your URI. Fix it like this:
  1. **Password in the URI**  
     The URI has the form `mongodb+srv://USERNAME:PASSWORD@host...`. The part after the colon and before `@` is the password. Make sure it is exactly the password you set in Atlas for that database user (Atlas → **Database Access** → your user → **Edit** to reset password if needed).
  2. **Special characters in the password**  
     If the password contains `@`, `#`, `:`, `/`, `%`, or similar, they must be **URL-encoded** in the URI or the connection will fail. Examples: `@` → `%40`, `#` → `%23`, `:` → `%3A`, `/` → `%2F`, `%` → `%25`.  
     Example: if your password is `p@ss#123`, in the URI write `p%40ss%23123`.
  3. **Replace `<password>`**  
     If you pasted the URI from Atlas and it still has the literal `<password>` in it, replace that with your real password (with special characters encoded as above).

- **"Server selection timeout" / "connection refused"**  
  - Confirm your IP is allowed in Atlas: **Network Access** → **Add IP Address** (or `0.0.0.0/0` for testing only).
  - Confirm the URI host and port match your cluster.
  - If you’re behind a firewall or VPN, try from another network.

- **"Connection failed" with no detail**  
  Check the **terminal** where the backend runs; the first connection attempt logs a more detailed error (e.g. `[MongoDB] Connection failed: ...`).

After fixing, restart the backend and call `GET /api/health/db` again to confirm `"ok": true`.
