"""Local Vosk speech recognition and Windows speech synthesis."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from collections.abc import Callable
from pathlib import Path

import pyttsx3
import sounddevice as sd
from vosk import KaldiRecognizer, Model

from config import SAMPLE_RATE, VOSK_MODEL_DIR

LOGGER = logging.getLogger(__name__)
WAKE_WORDS = ("hey acioz", "hey aci oz", "hey acyoz")


class AudioEngine:
    """Listen locally for a wake phrase and transcribe the next utterance."""

    def __init__(
        self,
        on_status: Callable[[str], None],
        on_command: Callable[[str], None],
        model_dir: Path = VOSK_MODEL_DIR,
    ) -> None:
        """Store callbacks and the path to the offline Vosk model."""
        self._on_status = on_status
        self._on_command = on_command
        self._model_dir = model_dir
        self._audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=32)
        self._speech_queue: queue.Queue[str] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the microphone listener in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen, name="acioz-audio", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Request a clean shutdown of the microphone listener."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)

    def speak(self, text: str) -> None:
        """Queue speech synthesis on the audio thread."""
        if text.strip():
            self._speech_queue.put(text.strip())

    def _audio_callback(self, data: bytes, _frames: int, _time: object, status: object) -> None:
        """Queue a microphone block without blocking the audio callback."""
        if status:
            LOGGER.warning("Microphone stream status: %s", status)
        try:
            self._audio_queue.put_nowait(data)
        except queue.Full:
            LOGGER.warning("Audio buffer full; dropping oldest microphone block.")
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(data)
            except queue.Empty:
                pass

    def _listen(self) -> None:
        """Run Vosk decoding and dispatch wake-word and command callbacks."""
        if not self._model_dir.is_dir():
            self._on_status(f"Vosk modeli bulunamadı: {self._model_dir}")
            return
        try:
            model = Model(str(self._model_dir))
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)
            recognizer.SetWords(False)
            speaker = pyttsx3.init()
            self._on_status("Dinlemede: Hey ACIÖZ")
            awaiting_command = False
            command_deadline = 0.0

            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=4_000,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            ):
                while not self._stop_event.is_set():
                    try:
                        speech = self._speech_queue.get_nowait()
                    except queue.Empty:
                        speech = ""
                    if speech:
                        speaker.say(speech)
                        speaker.runAndWait()

                    try:
                        audio = self._audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    if not recognizer.AcceptWaveform(audio):
                        continue

                    text = json.loads(recognizer.Result()).get("text", "").strip()
                    if not text:
                        continue
                    normalized = text.casefold().replace("ö", "o")

                    if awaiting_command:
                        if time.monotonic() > command_deadline:
                            awaiting_command = False
                            self._on_status("Dinlemede: Hey ACIÖZ")
                            continue
                        awaiting_command = False
                        self._on_status(f"Komut: {text}")
                        self._on_command(text)
                    elif any(word in normalized for word in WAKE_WORDS):
                        awaiting_command = True
                        command_deadline = time.monotonic() + 10
                        self._on_status("Buyurun efendim")
                        self._speech_queue.put("Buyurun efendim")
                        self._on_status("Komutunuz bekleniyor")
        except (OSError, RuntimeError, ValueError) as error:
            LOGGER.exception("Audio listener failed.")
            self._on_status(f"Mikrofon/dinleme hatası: {error}")
        except Exception as error:
            LOGGER.exception("Audio initialization failed.")
            self._on_status(f"Ses sistemi başlatılamadı: {error}")
