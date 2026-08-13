"""Keyword-based attendance detection using regex word boundaries."""

from __future__ import annotations

import re
import time
from typing import Any

from core.logger import BotLogger


class AttendanceDetector:
    """Detect attendance-related keywords in transcribed speech."""

    def __init__(self, config: dict[str, Any], logger: BotLogger) -> None:
        self._logger = logger
        self._config = config["attendance"]
        self._user_name = config["user"]["name"].strip()
        self._last_alert = 0.0

        # Load configured keywords
        keywords = list(self._config.get("keywords", []))

        # Ensure user's configured name is part of keywords (case-insensitive check)
        if self._user_name:
            user_name_lower = self._user_name.lower()
            if not any(word.lower() == user_name_lower for word in keywords):
                keywords.append(self._user_name)

        self._keywords = keywords
        self._case_sensitive = self._config.get("case_sensitive", False)
        self._cooldown = self._config.get("cooldown_seconds", 20)

    def check(self, text: str) -> bool:
        """Scan text for attendance keywords using regex word boundaries.

        Respects cooldown to avoid repeated alarms for the same class call.
        """
        if not self._config.get("enabled", True):
            return False

        flags = 0 if self._case_sensitive else re.IGNORECASE

        for keyword in self._keywords:
            if not keyword.strip():
                continue
            
            # Use \b (word boundary) to match full words only, avoiding substring matches
            pattern = rf"\b{re.escape(keyword.strip())}\b"
            
            if re.search(pattern, text, flags):
                now = time.time()
                # Enforce cooldown between alerts
                if now - self._last_alert < self._cooldown:
                    return False
                
                self._last_alert = now
                self._logger.info(
                    f"Attendance keyword matched: '{keyword}' in transcription: '{text.strip()}'"
                )
                return True

        return False
