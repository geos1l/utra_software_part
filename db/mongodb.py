"""MongoDB Atlas: insert_match, get_leaderboard, and connection check. No-op when MONGODB_URI is empty."""
from datetime import datetime
from typing import Any

_client = None
_connection_error: str | None = None


def _get_client():
    global _client, _connection_error
    if _client is not None:
        return _client
    if _connection_error is not None:
        return None
    from config.settings import Settings
    if not Settings.MONGODB_URI:
        return None
    try:
        from pymongo import MongoClient
        _client = MongoClient(Settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _connection_error = None
        return _client
    except Exception as e:
        _connection_error = str(e)
        print(f"[MongoDB] Connection failed: {_connection_error}")
        return None


def check_connection() -> tuple[bool, str | None]:
    """Test MongoDB connection. Returns (ok, error_message). Use at startup or for health checks."""
    client = _get_client()
    if client is None:
        from config.settings import Settings
        if not Settings.MONGODB_URI:
            return False, "MONGODB_URI not set"
        return False, _connection_error or "Connection failed"
    try:
        client.admin.command("ping")
        return True, None
    except Exception as e:
        return False, str(e)


def insert_match(doc: dict[str, Any]) -> dict[str, Any] | None:
    """Insert one match document. Returns inserted doc with _id, or None if MongoDB not configured/failed."""
    client = _get_client()
    if client is None:
        return None
    from config.settings import Settings
    db = client[Settings.MONGODB_DB_NAME]
    coll = db[Settings.MONGODB_COLLECTION]
    doc = dict(doc)
    doc["created_at"] = datetime.utcnow()
    try:
        result = coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc
    except Exception as e:
        print(f"[MongoDB] insert_match failed: {e}")
        return None


def get_leaderboard(limit: int = 100) -> list[dict[str, Any]]:
    """Return matches sorted by score_total desc. Same shape as in-memory leaderboard for frontend."""
    client = _get_client()
    if client is None:
        return []
    from config.settings import Settings
    db = client[Settings.MONGODB_DB_NAME]
    coll = db[Settings.MONGODB_COLLECTION]
    try:
        cursor = coll.find(
            {},
            {"_id": 0, "created_at": 1, "team_number": 1, "team_display": 1, "score_total": 1,
             "t_elapsed_s": 1, "obstacle_touches": 1, "completed_under_60": 1, "box_drop_1": 1, "box_drop_2": 1,
             "score_breakdown": 1},
        ).sort("score_total", -1).limit(limit)
        return list(cursor)
    except Exception as e:
        print(f"[MongoDB] get_leaderboard failed: {e}")
        return []