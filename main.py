"""Application entry point and Qt-thread-safe assistant controller."""

from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from audio_engine import AudioEngine
from brain_llm import LocalBrain
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
        self._audio = AudioEngine(
            on_status=self.status_changed.emit,
            on_command=self.handle_command,
        )
        self.status_changed.connect(window.set_status)
        self.response_ready.connect(window.set_response)
        window.send_button.clicked.connect(self._handle_typed_input)
        window.input_field.returnPressed.connect(self._handle_typed_input)

    def start(self) -> None:
        """Start local microphone listening and check Ollama availability."""
        self._audio.start()
        self._workers.submit(self._check_ollama)

    def _check_ollama(self) -> None:
        """Report local Ollama readiness without blocking the interface."""
        try:
            self._brain.health_check()
            self.status_changed.emit("Ollama yerel servisi hazır.")
        except Exception as error:
            LOGGER.warning("Ollama is unavailable: %s", error)
            self.status_changed.emit(
                "Ollama yerel servisi bulunamadı. Ollama'yı kurup başlat."
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

    def stop(self) -> None:
        """Stop audio and wait briefly for in-flight local requests."""
        self._audio.stop()
        self._workers.shutdown(wait=False, cancel_futures=True)


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
