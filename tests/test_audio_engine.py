"""Tests for native audio-engine path handling."""

import os
import unittest

from audio_engine import AudioEngine
from config import VOSK_MODEL_DIR


class AudioEngineTests(unittest.TestCase):
    """Verify configuration is compatible with Vosk's Windows path handling."""

    @unittest.skipUnless(os.name == "nt", "Windows Vosk path compatibility only.")
    def test_model_path_is_ascii_for_native_vosk(self) -> None:
        """Convert non-ASCII project paths to Windows short paths."""
        model_path = AudioEngine._model_path_for_vosk(VOSK_MODEL_DIR)

        self.assertTrue(model_path.isascii())


if __name__ == "__main__":
    unittest.main()
