"""Buffer payloads, rate-limit, drain 2+ to Gemini, then TTS."""
import time
import threading
from collections import deque
from .commentary_ai import CommentaryAI
from .tts import TTSSpeaker


class CommentaryRunner:
    """Hold payloads; when notable_event or FILLER_INTERVAL, drain up to N and commentate + TTS."""

    def __init__(
        self,
        commentary_ai: CommentaryAI,
        tts: TTSSpeaker,
        filler_interval_sec: float = 12.0,
        max_payloads_per_call: int = 3,
    ):
        self.commentary_ai = commentary_ai
        self.tts = tts
        self.filler_interval_sec = filler_interval_sec
        self.max_payloads_per_call = max_payloads_per_call
        self._buffer: deque[dict] = deque()
        self._lock = threading.Lock()
        self._last_commentary_time = 0.0
        self._in_flight = False
        self._stop = threading.Event()

    def push(self, payload: dict) -> None:
        with self._lock:
            self._buffer.append(payload)

    def _should_run(self) -> bool:
        with self._lock:
            if not self._buffer or self._in_flight:
                return False
            any_notable = any(p.get("notable_event") for p in self._buffer)
            if any_notable:
                return True
            return (time.time() - self._last_commentary_time) >= self.filler_interval_sec

    def _drain(self) -> list[dict]:
        with self._lock:
            n = min(len(self._buffer), self.max_payloads_per_call)
            return [self._buffer.popleft() for _ in range(n)]

    def tick(self) -> bool:
        """Process one batch if conditions met. Returns True if commentary was generated."""
        if not self._should_run():
            return False
        with self._lock:
            self._in_flight = True
        payloads = self._drain()
        if not payloads:
            with self._lock:
                self._in_flight = False
            return False
        text = self.commentary_ai.generate_commentary(payloads)
        self._last_commentary_time = time.time()
        if text:
            while self.tts.is_playing():
                time.sleep(0.1)
            self.tts.speak(text)
        with self._lock:
            self._in_flight = False
        return True

    def run_loop(self, poll_interval: float = 0.5) -> None:
        """Run tick in a loop until stop."""
        while not self._stop.is_set():
            self.tick()
            self._stop.wait(poll_interval)
