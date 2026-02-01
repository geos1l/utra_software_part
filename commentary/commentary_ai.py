"""Gemini commentary from match telemetry (OpenRouter, mirrors Hackhive llm_providers)."""
import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a live commentator for a robot competition. You receive match telemetry as JSON (team_id, score_total, t_elapsed_s, score_breakdown). You may receive one payload or several in chronological order as a JSON array. Base your commentary only on the data given; do not invent or guess. If you receive multiple updates, treat them as one short story in 1-2 hype lines. Output plain text only: 1-2 short hype lines, no JSON, no bullet points."""


class CommentaryAI:
    """Generate commentary from payload(s) via Gemini (OpenRouter)."""

    def __init__(self, api_key: str, model: str = "google/gemini-2.5-flash-lite"):
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
