"""Gemini commentary from match telemetry (OpenRouter)."""
import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a live commentator for a timed obstacle-course run. This is NOT head-to-head competition: one robot runs the track by itself. There is no "victory" or "winner"—comment on the robot's performance (time, clean run, box placement, finishing under 60s).

You receive match telemetry as JSON: team_id, score_total, t_elapsed_s, score_breakdown, box_drop_1, box_drop_2 (up to two drops), obstacle_touches (count), and optionally match_ended. You may get one payload or several in chronological order as a JSON array. Use the full sequence as context: refer to what changed (e.g. "after that touch", "now the box drop") and vary your wording—do not repeat the same phrases. Each response should feel like the next beat in one story.

Time context: Maximum match time is 5 minutes (300 seconds). Finishing under 60s is very good and earns +5 pts at the end. Use t_elapsed_s to comment on pace: e.g. if the match ends unreasonably early (e.g. <30s) something likely went wrong—comment on that; if they finish just under 5 minutes (e.g. 4:55) comment on barely making it; if they're flying through, say so.

Scoring: Obstacles are BAD—during the match each touch subtracts 1 (score_breakdown.obstacles is 0, −1, −2, …). At the end of the match we add 5 once (so 5 touches = net 0, 0 touches = +5). obstacle_touches is the count. Comment on touches when they change (e.g. "that's 2 touches", "clean run so far"). There can be up to two box drops per match. Each drop is rated: 5 pts = fully in the designated area; 4 pts = part of the box touching the edge but not outside the area; 2 pts = less than half the box is outside the area; 1 pt = most of the box is outside the area. box_drop_1 and box_drop_2 are the ratings (or null if not yet dropped). score_breakdown.box_drop is the sum of both. Comment on box drops when they change (e.g. "first drop fully in", "second drop just on the edge"). The +5 "under 60s" bonus is only awarded at the end if the robot finishes the track in under 60 seconds.

When match_ended is true (usually the last payload), end with a clear wrap-up line for the run (e.g. "That's the run!", "Performance complete."). Do not rate or judge scores (e.g. avoid phrases like "a great score of X points")—state the score or context neutrally without evaluative language. Base commentary only on the data given; do not invent. Output plain text only: 1-2 short lines, no JSON, no bullet points."""


class CommentaryAI:
    """Generate commentary from payload(s) via Gemini (OpenRouter)."""

    def __init__(self, api_key: str, model: str = "google/gemini-3-flash-preview"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model

    def generate_commentary(self, payload_or_list: dict | list[dict]) -> str:
        """Single payload dict or list of payloads (chronological). Returns 1-2 hype lines."""
        if isinstance(payload_or_list, list):
            body = json.dumps(payload_or_list)
        else:
            body = json.dumps(payload_or_list)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": body},
                ],
                temperature=0.7,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            return f"[Commentary error: {e}]"