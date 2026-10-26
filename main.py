"""Application entry point and Qt-thread-safe assistant controller."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from audio_engine import AudioEngine
from brain_llm import LocalBrain
from config import CHAT_MODEL, VISION_MODEL
from ui_engine import AssistantWindow
from vision_engine import VisionEngine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
LOGGER = logging.getLogger("acioz")


class AssistantController(QObject):
    """Connect background audio, local AI, vision, and the Qt interface."""

    status_changed = Signal(str)
    response_ready = Signal(str)

    def __init__(self, window: AssistantWindow) -> None:
        """Create services and route their events to Qt signals."""
        super().__init__()
        self._window = window
        self._brain = LocalBrain()
        self._vision = VisionEngine()
        self._workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="acioz")
        self._ollama_process: subprocess.Popen[bytes] | None = None
        self._audio = AudioEngine(
            on_status=self.status_changed.emit,
            on_command=self.handle_command,
        )
        self.status_changed.connect(window.set_status)
        self.response_ready.connect(window.set_response)
        self.response_ready.connect(self._speak_response)
        window.send_button.clicked.connect(self._handle_typed_input)
        window.input_field.returnPressed.connect(self._handle_typed_input)

    def start(self) -> None:
        """Start local microphone listening and check Ollama availability."""
        self._audio.start()
        self._workers.submit(self._check_ollama)

    def _check_ollama(self) -> None:
        """Start local Ollama if needed and report installed model readiness."""
        try:
            self._brain.health_check()
        except requests.RequestException:
            executable = self._find_ollama()
            if executable is None:
                self.status_changed.emit(
                    "Ollama bulunamadı. Kurulum için README.md dosyasına bak."
                )
                return

            environment = os.environ.copy()
            environment["OLLAMA_HOST"] = "127.0.0.1:11434"
            creation_flags = (
                subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            try:
                self._ollama_process = subprocess.Popen(
                    [str(executable), "serve"],
                    cwd=str(executable.parent),
                    env=environment,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags,
                )
                for _ in range(30):
                    if self._ollama_process.poll() is not None:
                        raise RuntimeError("Ollama servisi başlatılamadı.")
                    try:
                        self._brain.health_check()
                        break
                    except requests.RequestException:
                        time.sleep(1)
                else:
                    raise TimeoutError("Ollama servisi zamanında yanıt vermedi.")
            except (OSError, RuntimeError, TimeoutError) as error:
                LOGGER.exception("Local Ollama startup failed.")
                self.status_changed.emit(f"Ollama başlatılamadı: {error}")
                return

        try:
            installed_models = set(self._brain.list_models())
        except requests.RequestException as error:
            LOGGER.exception("Could not read local Ollama models.")
            self.status_changed.emit(f"Ollama modelleri okunamadı: {error}")
            return

        if CHAT_MODEL not in installed_models:
            self.status_changed.emit(
                f"Metin modeli eksik: {CHAT_MODEL}. README.md kurulum adımlarını uygula."
            )
        elif VISION_MODEL not in installed_models:
            self.status_changed.emit(
                f"Metin modeli hazır; kamera modeli eksik: {VISION_MODEL}."
            )
        else:
            self.status_changed.emit("Yerel metin ve kamera modelleri hazır.")

    @staticmethod
    def _find_ollama() -> Path | None:
        """Find a system or per-user Ollama executable."""
        installed_command = shutil.which("ollama")
        candidates = [
            Path(installed_command) if installed_command else None,
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs"
            / "Ollama"
            / "ollama.exe",
        ]
        return next(
            (candidate for candidate in candidates if candidate and candidate.is_file()),
            None,
        )

    def _handle_typed_input(self) -> None:
        """Submit a typed request using the same path as voice commands."""
        text = self._window.take_input()
        if text:
            self.handle_command(text)

    def handle_command(self, text: str) -> None:
        """Process a text request or capture a frame for vision analysis."""
        self.status_changed.emit("Yerel model düşünüyor…")
        self._workers.submit(self._process_command, text)

    def _process_command(self, text: str) -> None:
        """Run local inference and forward errors and results to the UI."""
        try:
            normalized = text.casefold()
            if "ne görüyor" in normalized or "kamerada" in normalized:
                image = self._vision.capture_jpeg()
                answer = self._brain.describe_image(
                    image, "Kamerada ne görüyorsun? Kısa ve nesnel yanıt ver."
                )
            else:
                answer = self._brain.answer(text)
            self.response_ready.emit(answer or "Model boş yanıt döndürdü.")
            self.status_changed.emit("Hazır.")
        except Exception as error:
            LOGGER.exception("Request processing failed.")
            self.response_ready.emit(f"Hata: {error}")
            self.status_changed.emit("İstek tamamlanamadı.")

    def _speak_response(self, text: str) -> None:
        """Queue the assistant response for local text-to-speech."""
        self._audio.speak(text)

    def stop(self) -> None:
        """Stop audio and wait briefly for in-flight local requests."""
        self._audio.stop()
        self._workers.shutdown(wait=False, cancel_futures=True)
        if self._ollama_process and self._ollama_process.poll() is None:
            self._ollama_process.terminate()
            try:
                self._ollama_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._ollama_process.kill()


def main() -> int:
    """Create and run the desktop application."""
    app = QApplication(sys.argv)
    window = AssistantWindow()
    controller = AssistantController(window)
    app.aboutToQuit.connect(controller.stop)
    window.show()
    controller.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
