"""In-memory match state: timer, team number, score breakdown (obstacles, completed_under_60, box_drops)."""
import time
import threading
from typing import Any

# Box drop rubric: up to two drops per match, each rated 5/4/2/1
# 5=fully in area, 4=part touching edge but not outside, 2=less than half outside, 1=most outside
BOX_DROP_POINTS = {
    "fully_in": 5,
    "edge_touching": 4,        # part touching edge but not outside area
    "partially_touching": 4,   # alias for edge_touching
    "less_than_half_out": 2,   # less than half the box outside area
    "mostly_out": 1,           # most of box outside area
}


class MatchState:
    """Single source of truth for match state. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()  # RLock so get_state() can call get_elapsed_s() etc. without deadlock
        self.timer_started_at: float | None = None
        self.timer_stopped_at_elapsed_s: float | None = None  # frozen time when match ended
        self.match_ended: bool = False
        self.team_number: str = "1"
        self.obstacle_touches: int = 0
        self.completed_under_60: bool = False
        self.box_drop_1: str | None = None  # first drop: fully_in | edge_touching | less_than_half_out | mostly_out | None
        self.box_drop_2: str | None = None  # second drop (optional)
        self._leaderboard: list[dict[str, Any]] = []

    def set_timer_started(self) -> None:
        """Start the match timer (call on key press or button). Idempotent after first call."""
        with self._lock:
            if self.timer_started_at is None:
                self.timer_started_at = time.time()

    def set_timer_stopped(self) -> None:
        """End the match: freeze timer at current elapsed, set match_ended."""
        with self._lock:
            elapsed = self.get_elapsed_s()
            self.timer_stopped_at_elapsed_s = elapsed
            self.timer_started_at = None
            self.match_ended = True

    def reset_for_new_match(self) -> None:
        """Clear timer and scoring state so the next Start match runs from 0 with no carryover."""
        with self._lock:
            self.timer_started_at = None
            self.timer_stopped_at_elapsed_s = None
            self.match_ended = False
            self.obstacle_touches = 0
            self.completed_under_60 = False
            self.box_drop_1 = None
            self.box_drop_2 = None

    def set_team_number(self, team_number: str | int) -> None:
        with self._lock:
            self.team_number = str(team_number)

    def set_breakdown(
        self,
        obstacle_touches: int | None = None,
        completed_under_60: bool | None = None,
        box_drop_1: str | None = None,
        box_drop_2: str | None = None,
    ) -> None:
        with self._lock:
            if obstacle_touches is not None:
                self.obstacle_touches = max(0, obstacle_touches)
            if completed_under_60 is not None:
                self.completed_under_60 = completed_under_60
            if box_drop_1 is not None:
                self.box_drop_1 = box_drop_1 if box_drop_1 in BOX_DROP_POINTS else None
            if box_drop_2 is not None:
                self.box_drop_2 = box_drop_2 if box_drop_2 in BOX_DROP_POINTS else None

    def get_elapsed_s(self) -> float:
        with self._lock:
            if self.timer_stopped_at_elapsed_s is not None:
                return self.timer_stopped_at_elapsed_s
            if self.timer_started_at is not None:
                return time.time() - self.timer_started_at
            return 0.0

    def compute_obstacle_points(self) -> int:
        """During match: subtract 1 per touch (-obstacle_touches). At end of match: add 5 once (net = 5 - obstacle_touches). Before Start: 0."""
        with self._lock:
            if not self.match_ended and self.timer_started_at is None:
                return 0
            if self.match_ended:
                return 5 - self.obstacle_touches  # scheduled +5 at end; 5 touches = net 0
            return -self.obstacle_touches  # during match: -1 per touch only

    def compute_time_bonus_points(self) -> int:
        """+5 only when match has ended and robot finished under 60s (bonus awarded at end)."""
        with self._lock:
            return 5 if (self.match_ended and self.completed_under_60) else 0

    def compute_box_drop_points(self) -> int:
        """Sum points for up to two box drops (each 5/4/2/1 per rubric)."""
        with self._lock:
            p1 = BOX_DROP_POINTS.get(self.box_drop_1 or "", 0)
            p2 = BOX_DROP_POINTS.get(self.box_drop_2 or "", 0)
            return p1 + p2

    def compute_score_total(self) -> int:
        return (
            self.compute_obstacle_points()
            + self.compute_time_bonus_points()
            + self.compute_box_drop_points()
        )

    def compute_score_breakdown(self) -> dict[str, int]:
        return {
            "obstacles": self.compute_obstacle_points(),
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
                "t_elapsed_s": int(round(elapsed)),
                "timer_running": self.timer_started_at is not None,
                "match_ended": self.match_ended,
                "score_total": self.compute_score_total(),
                "score_breakdown": breakdown,
                "obstacle_touches": self.obstacle_touches,
                "completed_under_60": self.completed_under_60,
                "box_drop_1": self.box_drop_1,
                "box_drop_2": self.box_drop_2,
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
            "box_drop_1": self.box_drop_1,
            "box_drop_2": self.box_drop_2,
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
