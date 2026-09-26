"""Ollama vision adapter.

The vision model describes the frame; it does not directly press keys. Keep
its output deliberately short: the old 100-token reasoning field caused the
truncated JSON failures in the source project.
"""

from __future__ import annotations

from typing import Optional

import ollama


PROMPT = r"""
Return ONE compact JSON object describing the current World of Warcraft combat frame.
Do not choose actions. Do not explain. Do not use Markdown.
Schema:
{"player_health_percent":0,"player_mana_percent":0,"pet_health_percent":0,"pet_alive":false,"target":{"name":null,"exists":false,"is_player":false,"is_elite":false,"is_rare":false,"health_percent":null,"level":null,"distance":"near"},"target_distance":"near","facing_target":true,"in_combat":true}
Rules: use null when unreadable; never invent a name; distance must be near or far; target means the currently selected target.
"""


class VisionClient:
    def __init__(self, model: str, base_url: str, timeout: int = 60):
        self.client = ollama.Client(
            host=base_url,
            timeout=timeout,
            trust_env=False,
        )
        self.model = model

    def describe(self, image_base64: str) -> str:
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": PROMPT, "images": [image_base64]}],
            options={
                "temperature": 0,
                "num_predict": 220,
                "num_ctx": 1536,
                "top_p": 1,
            },
            stream=False,
        )
        message = response.get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str):
            raise ValueError("Ollama returned non-text content")
        return content
