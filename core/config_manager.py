"""Thread-safe configuration manager for Google Meet Attendance Bot."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "2.0.0",
    "user": {
        "name": "User",
        "timezone": "Asia/Kolkata"
    },
    "browser": {
        "engine": "chromium",
        "headless": False,
        "persistent_profile": "./browser_profile",
        "slow_mo": 100,
        "maximize_window": True,
        "accept_permissions": True
    },
    "meeting": {
        "join_early_minutes": 5,
        "leave_late_minutes": 5,
        "auto_join": True,
        "mute_microphone": True,
        "disable_camera": True,
        "leave_after_class": True,
        "wait_for_host": True,
        "max_wait_minutes": 30,
        "retry_join": True,
        "retry_interval_seconds": 20,
        "max_join_retries": 3,
        "post_meeting_delay_seconds": 5,
        "close_browser_after_leave": True
    },
    "attendance": {
        "enabled": True,
        "keywords": ["attendance", "roll call", "present", "absent"],
        "case_sensitive": False,
        "cooldown_seconds": 20
    },
    "speech": {
        "enabled": True,
        "engine": "faster-whisper",
        "model": "base",
        "language": "en",
        "device": "auto",
        "beam_size": 5,
        "vad_filter": True,
        "save_transcript": True,
        "transcript_directory": "./transcripts"
    },
    "notifications": {
        "desktop": True,
        "sound": True,
        "popup": True,
        "flash_window": True,
        "repeat_alarm": True,
        "alarm_duration_seconds": 8
    },
    "alarm_path": "",
    "logging": {
        "enabled": True,
        "level": "INFO",
        "directory": "./logs",
        "save_console": True
    },
    "recording": {
        "enabled": True,
        "directory": "./recordings",
        "format": "wav",
        "chunk_seconds": 30,
        "samplerate": 48000,
        "channels": 2
    },
    "schedule": {
        "skip_weekends": True,
        "auto_start": True
    },
    "classes": []
}


class ConfigManager:
    """Manages bot configuration loaded from and saved to config.json thread-safely."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_PATH
        self._lock = threading.Lock()
        self._config: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload configuration from disk and merge with default config."""
        with self._lock:
            config = DEFAULT_CONFIG.copy()
            try:
                if self.config_path.exists():
                    with open(self.config_path, encoding="utf-8") as handle:
                        loaded = json.load(handle)
                        self._deep_merge(config, loaded)
                else:
                    logging.warning(f"Config file not found at {self.config_path}. Creating with defaults.")
                    self._save_to_disk(config)
            except Exception as exc:
                logging.error(f"Error loading config file: {exc}. Using default configuration.")
            
            self._config = config

    def get_config(self) -> dict[str, Any]:
        """Return a copy of the current configuration dictionary."""
        with self._lock:
            return json.loads(json.dumps(self._config))

    def save_config(self, new_config: dict[str, Any]) -> None:
        """Update the configuration dict and write it thread-safely to config.json on disk."""
        with self._lock:
            self._config = new_config
            self._save_to_disk(self._config)

    def _save_to_disk(self, config: dict[str, Any]) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2)
        except Exception as exc:
            logging.error(f"Failed to write config file to disk: {exc}")

    def _deep_merge(self, dict1: dict[str, Any], dict2: dict[str, Any]) -> None:
        """Recursively merge dict2 into dict1 in place."""
        for key, val in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(val, dict):
                self._deep_merge(dict1[key], val)
            else:
                dict1[key] = val

    def resolve_path(self, relative: str) -> Path:
        """Resolve a path relative to the project root directory."""
        path = Path(relative)
        if path.is_absolute():
            return path
        return BASE_DIR / path

    def ensure_directories(self) -> dict[str, Path]:
        """Create necessary application directories and return their resolved paths."""
        config = self.get_config()
        paths = {
            "profile": self.resolve_path(config["browser"]["persistent_profile"]),
            "recordings": self.resolve_path(config["recording"]["directory"]),
            "transcripts": self.resolve_path(config["speech"]["transcript_directory"]),
            "logs": self.resolve_path(config["logging"]["directory"]),
            "chunks": self.resolve_path(config["recording"]["directory"]) / "chunks",
        }
        for directory in paths.values():
            directory.mkdir(parents=True, exist_ok=True)
        return paths
