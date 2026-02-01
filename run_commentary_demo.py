"""Demo: push mock payloads to commentary runner; test Gemini + TTS. No CV imports.

=== DEMO ONLY: Remove or replace this file when wiring real CV/telemetry. ===
All payloads below are simulated to mimic a full game (0 -> obstacle points -> box drop -> time bonus).
"""
import sys
import time
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import Settings
from commentary.commentary_ai import CommentaryAI
from commentary.commentary_runner import CommentaryRunner
from commentary.tts import TTSSpeaker


def main():
    missing = Settings.validate()
    if missing:
        print(f"Missing env: {missing}. Set in .env and retry.")
        sys.exit(1)
    ai = CommentaryAI(Settings.GEMINI_API_KEY, Settings.GEMINI_MODEL)
    tts = TTSSpeaker(Settings.ELEVENLABS_API_KEY, Settings.ELEVENLABS_VOICE)
    runner = CommentaryRunner(
        ai, tts,
        filler_interval_sec=Settings.FILLER_INTERVAL_SEC,
        max_payloads_per_call=Settings.MAX_PAYLOADS_PER_CALL,
    )

    # ========== DEMO: Simulated full game sequence (remove when using real telemetry) ==========
    # Start: 0 points, timer at 0
    # -> Obstacle: 0 touches -> 5 pts
    # -> Box drop: fully in -> +5 pts (total 10)
    # -> Obstacle touch: 1 touch -> 4 pts obstacle, total 9
    # -> Box drop: partially touching -> 4 pts box (total 8 from box), keep obstacle 4 -> total 12
    # -> Completed under 60s: true -> +5 (total 17)
    # Each push is one "update"; we send a batch so Gemini can comment on the story.

    demo_payloads = [
        # DEMO: Match start, 0 points
        {
            "team_id": "TEAM_01",
            "score_total": 0,
            "t_elapsed_s": 0.0,
            "score_breakdown": {"obstacle": 0, "completed_under_60": 0, "box_drop": 0},
            "notable_event": True,
        },
        # DEMO: First scoring — obstacle course clean (5 pts)
        {
            "team_id": "TEAM_01",
            "score_total": 5,
            "t_elapsed_s": 12.0,
            "score_breakdown": {"obstacle": 5, "completed_under_60": 0, "box_drop": 0},
            "notable_event": True,
        },
        # DEMO: Box drop fully in (+5)
        {
            "team_id": "TEAM_01",
            "score_total": 10,
            "t_elapsed_s": 28.0,
            "score_breakdown": {"obstacle": 5, "completed_under_60": 0, "box_drop": 5},
            "notable_event": True,
        },
        # DEMO: One obstacle touch (obstacle 4, total 9)
        {
            "team_id": "TEAM_01",
            "score_total": 9,
            "t_elapsed_s": 35.0,
            "score_breakdown": {"obstacle": 4, "completed_under_60": 0, "box_drop": 5},
            "notable_event": True,
        },
        # DEMO: Box adjusted to partially touching (box 4, total 12)
        {
            "team_id": "TEAM_01",
            "score_total": 12,
            "t_elapsed_s": 48.0,
            "score_breakdown": {"obstacle": 4, "completed_under_60": 0, "box_drop": 4},
            "notable_event": True,
        },
        # DEMO: Finish under 60s (+5 time bonus, total 17)
        {
            "team_id": "TEAM_01",
            "score_total": 17,
            "t_elapsed_s": 58.5,
            "score_breakdown": {"obstacle": 4, "completed_under_60": 5, "box_drop": 4},
            "notable_event": True,
        },
    ]
    # ========== END DEMO payloads ==========

    for p in demo_payloads:
        runner.push(p)

    # DEMO: Run commentary for each batch (up to MAX_PAYLOADS_PER_CALL per tick)
    print("Running commentary (DEMO: simulated full game)...")
    for _ in range(3):  # Up to 3 batches for 6 payloads
        if runner.tick():
            while tts.is_playing():
                time.sleep(0.1)
        else:
            break
    print("Done. (Remove run_commentary_demo.py or the DEMO payloads when using real telemetry.)")


if __name__ == "__main__":
    main()
