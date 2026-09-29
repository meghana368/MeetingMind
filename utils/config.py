"""Configuration loaded from environment variables (and an optional .env file).

Secrets are never logged or displayed; only their presence is checked.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HINDSIGHT_URL = "https://api.hindsight.vectorize.io"
DEFAULT_BANK_ID = "meetingmind"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"  # the single place the default lives


@dataclass(frozen=True)
class Settings:
    """Validated application settings."""

    hindsight_api_key: str
    hindsight_base_url: str
    hindsight_bank_id: str
    groq_api_key: str
    groq_model: str
    data_dir: Path

    @property
    def is_local_hindsight(self) -> bool:
        """True when Hindsight runs on this machine (no API key needed)."""
        host = urlparse(self.hindsight_base_url).hostname or ""
        return host in {"localhost", "127.0.0.1", "0.0.0.0"}

    def missing_configuration(self) -> List[str]:
        """Return user-friendly messages for every missing required setting."""
        problems: List[str] = []
        if not self.groq_api_key:
            problems.append(
                "Groq API key is not configured. Add GROQ_API_KEY to your .env file."
            )
        if not self.hindsight_api_key and not self.is_local_hindsight:
            problems.append(
                "Hindsight API key is not configured. Add HINDSIGHT_API_KEY to your .env file."
            )
        return problems


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """Build Settings from ``env`` (defaults to the process env + .env file)."""
    if env is None:
        load_dotenv(PROJECT_ROOT / ".env")
        env = os.environ
    data_dir = env.get("MEETINGMIND_DATA_DIR") or str(PROJECT_ROOT / "data")
    return Settings(
        hindsight_api_key=(env.get("HINDSIGHT_API_KEY") or "").strip(),
        hindsight_base_url=(env.get("HINDSIGHT_BASE_URL") or DEFAULT_HINDSIGHT_URL).strip(),
        hindsight_bank_id=(env.get("HINDSIGHT_BANK_ID") or DEFAULT_BANK_ID).strip(),
        groq_api_key=(env.get("GROQ_API_KEY") or "").strip(),
        groq_model=(env.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL).strip(),
        data_dir=Path(data_dir),
    )
