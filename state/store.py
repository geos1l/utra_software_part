"""In-memory match state: timer, team number, score breakdown (obstacle, completed_under_60, box_drop)."""
import time
import threading
from typing import Any

# Box drop points: fully_in=5, partially_touching=4, mostly_out=1, None=0
BOX_DROP_POINTS = {"fully_in": 5, "partially_touching": 4, "mostly_out": 1}


class MatchState:
    """Single source of truth for match state. Thread-safe."""

    def __init__(self):
        self._lock = threading.Lock()
        self.timer_started_at: float | None = None
        self.team_number: str = "1"
        self.obstacle_touches: int = 0
        self.completed_under_60: bool = False
        self.box_drop: str | None = None  # "fully_in" | "partially_touching" | "mostly_out" | None
        self._leaderboard: list[dict[str, Any]] = []

    def set_timer_started(self) -> None:
        """Start the timer (call on key press). Idempotent after first call."""
        with self._lock:
            if self.timer_started_at is None:
                self.timer_started_at = time.time()

    def set_team_number(self, team_number: str | int) -> None:
        with self._lock:
            self.team_number = str(team_number)

    def set_breakdown(
        self,
        obstacle_touches: int | None = None,
        completed_under_60: bool | None = None,
        box_drop: str | None = None,
    ) -> None:
        with self._lock:
            if obstacle_touches is not None:
                self.obstacle_touches = max(0, obstacle_touches)
            if completed_under_60 is not None:
                self.completed_under_60 = completed_under_60
            if box_drop is not None:
                self.box_drop = box_drop if box_drop in BOX_DROP_POINTS else None

    def get_elapsed_s(self) -> float:
        with self._lock:
            if self.timer_started_at is None:
                return 0.0
            return time.time() - self.timer_started_at

    def compute_obstacle_points(self) -> int:
        """max(0, 5 - obstacle_touches)."""
        with self._lock:
            return max(0, 5 - self.obstacle_touches)

    def compute_time_bonus_points(self) -> int:
        """+5 if completed_under_60 else 0."""
        with self._lock:
            return 5 if self.completed_under_60 else 0

    def compute_box_drop_points(self) -> int:
        with self._lock:
            return BOX_DROP_POINTS.get(self.box_drop or "", 0)

    def compute_score_total(self) -> int:
        return (
            self.compute_obstacle_points()
            + self.compute_time_bonus_points()
            + self.compute_box_drop_points()
        )

    def compute_score_breakdown(self) -> dict[str, int]:
        return {
            "obstacle": self.compute_obstacle_points(),
            "completed_under_60": self.compute_time_bonus_points(),
            "box_drop": self.compute_box_drop_points(),
        }

    def get_state(self) -> dict[str, Any]:
        """Full state for API/HUD: team_number, timer, score, breakdown."""
        with self._lock:
            elapsed = self.get_elapsed_s()
            breakdown = self.compute_score_breakdown()
            return {
                "team_number": self.team_number,
                "team_display": f"Team {self.team_number}",
                "timer_started_at": self.timer_started_at,
                "t_elapsed_s": round(elapsed, 2),
                "timer_running": self.timer_started_at is not None,
                "score_total": self.compute_score_total(),
                "score_breakdown": breakdown,
                "obstacle_touches": self.obstacle_touches,
                "completed_under_60": self.completed_under_60,
                "box_drop": self.box_drop,
            }

    def save_run_to_leaderboard(self) -> dict[str, Any]:
        """Append current run to leaderboard; return saved entry."""
        entry = {
            "team_number": self.team_number,
            "team_display": f"Team {self.team_number}",
            "score_total": self.compute_score_total(),
            "score_breakdown": self.compute_score_breakdown(),
            "t_elapsed_s": round(self.get_elapsed_s(), 2),
            "obstacle_touches": self.obstacle_touches,
            "completed_under_60": self.completed_under_60,
            "box_drop": self.box_drop,
        }
        with self._lock:
            self._leaderboard.append(entry)
        return entry

    def get_leaderboard(self) -> list[dict[str, Any]]:
        """Leaderboard sorted by score_total descending."""
        with self._lock:
            return sorted(
                list(self._leaderboard),
                key=lambda x: x["score_total"],
                reverse=True,
            )


# Singleton used by web app and stream
match_state = MatchState()
