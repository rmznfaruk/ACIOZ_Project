"""Local-only Ollama chat and vision client."""

import base64
import json
from typing import Any

import requests

from config import CHAT_MODEL, OLLAMA_URL, VISION_MODEL
from system_tools import SystemTools


SYSTEM_PROMPT = (
    "Sen ACIÖZ'sün; Türkçe, kısa, teknik ve doğrudan yanıt ver. "
    "Yalnızca kullanıcı isteğiyle ilgili, sunulan yerel araçları kullan. "
    "Dosya silme veya değiştirme yeteneğin yok; böyle bir istekte bunu açıkça belirt."
)


class LocalBrain:
    """Send chat and image requests only to the local Ollama server."""

    def __init__(
        self,
        tools: SystemTools | None = None,
        base_url: str = OLLAMA_URL,
        chat_model: str = CHAT_MODEL,
        vision_model: str = VISION_MODEL,
    ) -> None:
        """Initialize local endpoint, model names, and safe desktop tools."""
        self._session = requests.Session()
        self._base_url = base_url.rstrip("/")
        self._chat_model = chat_model
        self._vision_model = vision_model
        self._tools = tools or SystemTools()

    def health_check(self) -> bool:
        """Return whether the local Ollama service is responding."""
        response = self._session.get(f"{self._base_url}/api/tags", timeout=3)
        response.raise_for_status()
        return True

    def list_models(self) -> list[str]:
        """Return names of models already available on the local machine."""
        response = self._session.get(f"{self._base_url}/api/tags", timeout=5)
        response.raise_for_status()
        return [model["name"] for model in response.json().get("models", [])]

    def _chat(
        self, messages: list[dict[str, Any]], model: str, tools: list[dict[str, object]] | None = None
    ) -> dict[str, Any]:
        """Send one non-streaming chat request to the local Ollama API."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 384},
        }
        if tools:
            payload["tools"] = tools
        response = self._session.post(
            f"{self._base_url}/api/chat", json=payload, timeout=(5, 180)
        )
        response.raise_for_status()
        return response.json()["message"]

    def answer(self, prompt: str) -> str:
        """Answer a text request and execute only the exposed safe local tools."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        schemas = self._tools.tool_definitions()

        for _ in range(3):
            message = self._chat(messages, self._chat_model, schemas)
            messages.append(message)
            calls = message.get("tool_calls", [])
            if not calls:
                return str(message.get("content", "")).strip()

            for call in calls:
                function = call.get("function", {})
                name = str(function.get("name", ""))
                arguments = function.get("arguments", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                try:
                    result = self._tools.execute(name, arguments)
                except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
                    result = f"İşlem gerçekleştirilemedi: {error}"
                messages.append(
                    {"role": "tool", "name": name, "content": str(result)}
                )

        return str(messages[-1].get("content", "İşlem tamamlanamadı."))

    def describe_image(self, image: bytes, prompt: str) -> str:
        """Ask the configured local vision model to describe a camera frame."""
        image_data = base64.b64encode(image).decode("ascii")
        message = self._chat(
            [
                {
                    "role": "system",
                    "content": "Görüntüyü yalnızca görülebilen bilgilere dayanarak Türkçe ve net biçimde anlat.",
                },
                {"role": "user", "content": prompt, "images": [image_data]},
            ],
            self._vision_model,
        )
        return str(message.get("content", "")).strip()
