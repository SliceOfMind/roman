from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except Exception:  # optional dependency support
    OpenAI = None


class OpenAIClient:
    def __init__(self, api_key: str | None):
        self.enabled = bool(api_key and OpenAI)
        self._client = OpenAI(api_key=api_key) if self.enabled and OpenAI else None
        if api_key and not OpenAI:
            logger.warning("OPENAI_API_KEY задан, но пакет openai не установлен. Работаем в fallback-режиме.")

    def generate_arguments(self, topic: str) -> dict[str, str] | None:
        if not self.enabled or not self._client:
            return None
        prompt = (
            "Ты редактор юридического Telegram-канала. Для вопроса сформируй: аргумент за, аргумент против,"
            " и краткий вывод. Ответ строго JSON с ключами pro, con, synthesis."
            f"\nВопрос: {topic}"
        )
        try:
            response = self._client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                temperature=0.5,
            )
            text = response.output_text
        except Exception as exc:
            logger.warning("OpenAI generation failed: %s", exc)
            return None

        try:
            import json

            payload = json.loads(text)
            return {
                "pro": payload.get("pro", ""),
                "con": payload.get("con", ""),
                "synthesis": payload.get("synthesis", ""),
            }
        except Exception:
            logger.warning("OpenAI returned non-JSON content, using raw fallback")
            return {"pro": text, "con": "", "synthesis": ""}
