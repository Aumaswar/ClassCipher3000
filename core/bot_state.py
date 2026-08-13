"""Shared thread-safe state container for Google Meet Attendance Bot."""

from __future__ import annotations

import queue
import threading
from datetime import datetime
from typing import Any

from playwright.sync_api import Page


class BotState:
    """Thread-safe state container for communication between UI and bot runner threads."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

        # Primitives with locks
        self._bot_active = False
        self._status_text = "Stopped"
        self._countdown_text = "N/A"
        self._current_class_label = "None"
        self._current_meeting_link = ""
        self._force_action: str | None = None
        self._attendance_marked = False
        self._audio_peak = 0.0
        self._completed_classes: set[tuple[str, str, str]] = set()
        self._last_completed_date = datetime.now().date()
        
        # Thread-safe queues
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.transcript_queue: queue.Queue[str] = queue.Queue()
        self.alert_queue: queue.Queue[tuple[str, str]] = queue.Queue()  # (subject, text)

        # Reference to active Playwright page to allow UI commands to interact with browser
        self.active_page: Page | None = None

    @property
    def audio_peak(self) -> float:
        """Peak amplitude of captured audio in the last block (0.0 to 1.0)."""
        with self._lock:
            return self._audio_peak

    @audio_peak.setter
    def audio_peak(self, val: float) -> None:
        with self._lock:
            self._audio_peak = val

    @property
    def completed_classes(self) -> set[tuple[str, str, str]]:
        """Set of completed class IDs, automatically cleared on date change."""
        with self._lock:
            today = datetime.now().date()
            if today != self._last_completed_date:
                self._completed_classes.clear()
                self._last_completed_date = today
            return self._completed_classes

    @property
    def attendance_marked(self) -> bool:
        """True if user marked their attendance as completed for the current session."""
        with self._lock:
            return self._attendance_marked

    @attendance_marked.setter
    def attendance_marked(self, val: bool) -> None:
        with self._lock:
            self._attendance_marked = val

    @property
    def bot_active(self) -> bool:
        """True if the background bot thread should be running."""
        with self._lock:
            return self._bot_active

    @bot_active.setter
    def bot_active(self, val: bool) -> None:
        with self._lock:
            self._bot_active = val

    @property
    def status_text(self) -> str:
        """General status message shown on the Home dashboard."""
        with self._lock:
            return self._status_text

    @status_text.setter
    def status_text(self, val: str) -> None:
        with self._lock:
            self._status_text = val

    @property
    def countdown_text(self) -> str:
        """Formatted time remaining (e.g. HH:MM:SS) until the next class opens."""
        with self._lock:
            return self._countdown_text

    @countdown_text.setter
    def countdown_text(self, val: str) -> None:
        with self._lock:
            self._countdown_text = val

    @property
    def current_class_label(self) -> str:
        """Label describing the currently active or next class."""
        with self._lock:
            return self._current_class_label

    @current_class_label.setter
    def current_class_label(self, val: str) -> None:
        with self._lock:
            self._current_class_label = val

    @property
    def current_meeting_link(self) -> str:
        """Link of the current or upcoming meeting."""
        with self._lock:
            return self._current_meeting_link

    @current_meeting_link.setter
    def current_meeting_link(self, val: str) -> None:
        with self._lock:
            self._current_meeting_link = val

    @property
    def force_action(self) -> str | None:
        """Command override set by UI (e.g. 'join_now', 'leave_meeting')."""
        with self._lock:
            return self._force_action

    @force_action.setter
    def force_action(self, val: str | None) -> None:
        with self._lock:
            self._force_action = val


# Global shared state instance
state = BotState()
