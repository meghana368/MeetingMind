"""Groq LLM service: prompts in, validated Pydantic objects out."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from utils.config import Settings
from utils.errors import LLMError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)
MAX_ATTEMPTS = 2


def parse_json_object(raw: str) -> Dict[str, Any]:
    """Parse a JSON object from LLM text, tolerating code fences and chatter."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("No JSON object found in model output.")
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("Model output is not a JSON object.")
    return data


class LLMService:
    """Thin wrapper around the Groq chat API with structured-output handling."""

    def __init__(self, settings: Settings, client: Optional[Any] = None) -> None:
        self._settings = settings
        self._client = client  # injectable for tests

    def _get_client(self) -> Any:
        if self._client is None:
            if not self._settings.groq_api_key:
                raise LLMError(
                    "Groq API key is not configured. Add GROQ_API_KEY to your .env file."
                )
            try:
                from groq import Groq
            except ImportError as exc:
                raise LLMError(
                    "The Groq client is not installed. Run: pip install -r requirements.txt"
                ) from exc
            self._client = Groq(api_key=self._settings.groq_api_key)
        return self._client

    def _translate(self, exc: Exception) -> str:
        name, text = type(exc).__name__.lower(), str(exc).lower()
        if "authentication" in name or "401" in text or "invalid api key" in text:
            return "Groq rejected the API key. Check GROQ_API_KEY in your .env file."
        if "ratelimit" in name or "429" in text:
            return "Groq rate limit reached. Wait a few seconds and try again."
        if "connection" in name or "timeout" in name:
            return "Could not reach Groq. Check your internet connection."
        if "model" in text and any(k in text for k in ("not found", "decommissioned", "does not exist")):
            return f"Groq could not use model '{self._settings.groq_model}'. Check GROQ_MODEL."
        return "The Groq API returned an unexpected error. See the application log for details."

    def _complete(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self._settings.groq_model,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except LLMError:
            raise
        except Exception as exc:
            logger.exception("Groq request failed")
            raise LLMError(self._translate(exc)) from exc

    def generate_structured(self, system_prompt: str, user_prompt: str, model_cls: Type[T]) -> T:
        """Call the LLM and return a validated ``model_cls`` instance.

        Retries once with a correction message if the output is malformed.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        for attempt in range(1, MAX_ATTEMPTS + 1):
            raw = self._complete(messages)
            try:
                return model_cls.model_validate(parse_json_object(raw))
            except ValueError as exc:  # JSONDecodeError and pydantic ValidationError
                logger.warning("Malformed LLM output (attempt %d): %s", attempt, exc)
                messages = messages + [
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": "That was not valid JSON matching the schema. "
                        "Return ONLY the corrected JSON object.",
                    },
                ]
        raise LLMError(
            "The AI model returned a response MeetingMind could not understand. Please try again."
        )
