"""Hindsight memory service - the ONLY module that talks to the Hindsight SDK."""
from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional, Tuple

from utils.config import Settings
from utils.errors import HindsightError

logger = logging.getLogger(__name__)


class HindsightService:
    """Retain, recall and reflect on memories in a single Hindsight bank."""

    def __init__(self, settings: Settings, client: Optional[Any] = None) -> None:
        self._settings = settings
        self._client = client  # injectable for tests
        self._bank_ready = False

    @property
    def bank_id(self) -> str:
        return self._settings.hindsight_bank_id

    # ---- client plumbing -------------------------------------------------
    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._settings.hindsight_api_key and not self._settings.is_local_hindsight:
            raise HindsightError(
                "Hindsight API key is not configured. Add HINDSIGHT_API_KEY to your .env file."
            )
        try:
            from hindsight_client import Hindsight
        except ImportError as exc:
            raise HindsightError(
                "The Hindsight client is not installed. Run: pip install -r requirements.txt"
            ) from exc
        kwargs = {"base_url": self._settings.hindsight_base_url, "timeout": 60.0}
        if self._settings.hindsight_api_key:
            kwargs["api_key"] = self._settings.hindsight_api_key
        self._client = Hindsight(**kwargs)
        return self._client

    def _translate(self, exc: Exception) -> str:
        """Turn an SDK/network exception into a safe, friendly message."""
        text = f"{type(exc).__name__} {exc}".lower()
        if any(k in text for k in ("401", "403", "unauthorized", "forbidden", "invalid api key")):
            return "Hindsight rejected the API key. Check HINDSIGHT_API_KEY in your .env file."
        if any(k in text for k in ("connect", "timeout", "timed out", "resolution", "refused", "network")):
            return (
                f"Could not reach Hindsight at {self._settings.hindsight_base_url}. "
                "Check your internet connection and HINDSIGHT_BASE_URL."
            )
        if "404" in text or "not found" in text:
            return f"Hindsight memory bank '{self.bank_id}' was not found or is unavailable."
        return "Hindsight returned an unexpected error. See the application log for details."

    def _run(self, operation: Callable[[Any], Any], description: str) -> Any:
        client = self._get_client()
        try:
            return operation(client)
        except HindsightError:
            raise
        except Exception as exc:  # SDK raises many exception types
            logger.exception("Hindsight %s failed", description)
            raise HindsightError(self._translate(exc)) from exc

    # ---- public API ------------------------------------------------------
    def ensure_bank(self) -> None:
        """Create the memory bank if needed (safe to call repeatedly)."""
        if self._bank_ready:
            return
        client = self._get_client()
        try:
            client.create_bank(bank_id=self.bank_id, name="MeetingMind")
        except Exception as exc:
            if any(k in str(exc).lower() for k in ("already exists", "409", "conflict")):
                logger.info("Bank %s already exists", self.bank_id)
            else:
                logger.exception("Hindsight create_bank failed")
                raise HindsightError(self._translate(exc)) from exc
        self._bank_ready = True

    def health_check(self) -> Tuple[bool, str]:
        """Return (ok, message) describing whether Hindsight is usable."""
        try:
            self.ensure_bank()
        except HindsightError as exc:
            return False, str(exc)
        return True, f"Connected to Hindsight. Memory bank: '{self.bank_id}'."

    def retain_memory(
        self, content: str, context: Optional[str] = None, timestamp: Optional[str] = None
    ) -> None:
        """Store one memory statement in Hindsight."""
        self.ensure_bank()
        kwargs = {"bank_id": self.bank_id, "content": content}
        if context:
            kwargs["context"] = context
        if timestamp:
            kwargs["timestamp"] = timestamp
        self._run(lambda c: c.retain(**kwargs), "retain")

    def recall_memories(self, query: str, max_results: int = 30) -> List[str]:
        """Recall memories relevant to ``query`` as plain-text statements."""
        self.ensure_bank()
        response = self._run(lambda c: c.recall(bank_id=self.bank_id, query=query), "recall")
        return self._extract_texts(response)[:max_results]

    def reflect_on_memories(self, query: str) -> str:
        """Ask Hindsight to reason over its memories and return an answer."""
        self.ensure_bank()
        response = self._run(lambda c: c.reflect(bank_id=self.bank_id, query=query), "reflect")
        return str(getattr(response, "text", None) or response or "").strip()

    @staticmethod
    def _extract_texts(response: Any) -> List[str]:
        """Normalise SDK recall output into a de-duplicated list of strings."""
        results = getattr(response, "results", response) or []
        texts: List[str] = []
        for item in results:
            text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
            text = (text or "").strip()
            if text and text not in texts:
                texts.append(text)
        return texts
