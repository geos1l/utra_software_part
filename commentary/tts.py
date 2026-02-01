"""ElevenLabs TTS (mirrors Hackhive Project 2026 src/audio/speaker.py)."""
from elevenlabs.client import ElevenLabs
import numpy as np
import sounddevice as sd
import threading
import time


class TTSSpeaker:
    """Text-to-speech using ElevenLabs API."""

    VOICES = {
        "Guy": "34lPwSZ54D8fWbX1aHzk",
        "Goat Gemini": "Q2ELiWzbuj5F0eFHXK6S",
        "Rex Thunder": "mtrellq69YZsNwzUSyXh",
        "rachel": "EXAVITQu4vr4xnSDxMaL",
        "adam": "pNInz6obpgDQGcFmaJgB",
        "bella": "EXAVITQu4vr4xnSDxMaL",
        "josh": "TxGEqnHWrfWFTfGW9XjX",
    }
    MODELS = {
        "fast": "eleven_flash_v2_5",
        "quality": "eleven_multilingual_v2",
    }
    SAMPLE_RATE = 16000

    def __init__(self, api_key: str, voice: str = "Guy", model: str = "fast"):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = self.VOICES.get(voice, voice)
        self.model_id = self.MODELS.get(model, model)
        self._playback_thread = None
        self._is_playing = False
        self._stop_playback = threading.Event()

    def speak(self, text: str) -> None:
        self.stop()
        pcm_data = self._generate_pcm(text)
        audio_array = np.frombuffer(pcm_data, dtype=np.int16)
        self._stop_playback.clear()
        self._is_playing = True
        sd.play(audio_array, samplerate=self.SAMPLE_RATE)

        def _monitor():
            try:
                while True:
                    stream = sd.get_stream()
                    if stream is None or not stream.active:
                        break
                    if self._stop_playback.is_set():
                        sd.stop()
                        break
                    time.sleep(0.1)
            except Exception:
                pass
            finally:
                self._is_playing = False

        self._playback_thread = threading.Thread(target=_monitor, daemon=True)
        self._playback_thread.start()

    def _generate_pcm(self, text: str) -> bytes:
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format="pcm_16000",
        )
        return b"".join(audio)

    def stop(self) -> None:
        if self._is_playing:
            self._stop_playback.set()
            sd.stop()
            self._is_playing = False
            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=0.5)

    def is_playing(self) -> bool:
        return self._is_playing
