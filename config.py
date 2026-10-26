"""Shared configuration for the local ACIÖZ assistant."""

from pathlib import Path
import os

PROJECT_DIR = Path(__file__).resolve().parent
VOSK_MODEL_DIR = Path(
    os.getenv(
        "ACIOZ_VOSK_MODEL",
        str(PROJECT_DIR / "models" / "vosk-model-small-tr-0.3"),
    )
)
OLLAMA_URL = "http://127.0.0.1:11434"
CHAT_MODEL = os.getenv("ACIOZ_CHAT_MODEL", "qwen3:4b")
VISION_MODEL = os.getenv("ACIOZ_VISION_MODEL", "qwen2.5vl:3b")
SAMPLE_RATE = 16_000
