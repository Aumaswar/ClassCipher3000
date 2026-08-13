"""Daily file logging with console and thread-safe UI queue outputs."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, date
from pathlib import Path


class BotLogger:
    """Application logger that writes to daily log files, console, and GUI log queue."""

    def __init__(self, log_dir: Path, level: str = "INFO", console: bool = True) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger("meet_bot")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._logger.handlers.clear()
        self._logger.propagate = False

        self._formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._current_date: date = datetime.now().date()
        self._console = console
        
        self._setup_handlers()

    def _current_log_file(self) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"bot_{date_str}.log"

    def _setup_handlers(self) -> None:
        self._logger.handlers.clear()

        # Daily file handler
        file_handler = logging.FileHandler(
            self._current_log_file(),
            encoding="utf-8",
        )
        file_handler.setFormatter(self._formatter)
        self._logger.addHandler(file_handler)

        # Console output
        if self._console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self._formatter)
            self._logger.addHandler(console_handler)

    def _rotate_if_needed(self) -> None:
        """Rotate daily log file if the calendar date changes."""
        today = datetime.now().date()
        if today != self._current_date:
            self._current_date = today
            self._setup_handlers()

    def _push_to_gui(self, level: str, message: str) -> None:
        """Push log message to the global UI bot_state log queue."""
        try:
            from core.bot_state import state
            time_str = datetime.now().strftime("%H:%M:%S")
            state.log_queue.put(f"[{time_str}] {level} | {message}")
        except Exception:
            pass

    def info(self, message: str) -> None:
        """Log an informational message."""
        self._rotate_if_needed()
        self._logger.info(message)
        self._push_to_gui("INFO", message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._rotate_if_needed()
        self._logger.warning(message)
        self._push_to_gui("WARNING", message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self._rotate_if_needed()
        self._logger.error(message)
        self._push_to_gui("ERROR", message)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._rotate_if_needed()
        self._logger.debug(message)
        self._push_to_gui("DEBUG", message)
