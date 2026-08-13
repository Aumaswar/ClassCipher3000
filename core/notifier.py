"""Windows desktop notifications, alarms, and message box alerts."""

from __future__ import annotations

import ctypes
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logger import BotLogger


class Notifier:
    """Show Windows notifications, play alarms, and show popups when attendance is detected."""

    def __init__(self, config: dict[str, Any], logger: BotLogger) -> None:
        self._config = config["notifications"]
        self._logger = logger
        self._alarm_path = config.get("alarm_path", "")

    def alert_attendance(self, subject: str, matched_text: str) -> None:
        """Trigger all configured notifications asynchronously."""
        title = f"Attendance Alert — {subject}"
        message = f"Possible roll call detected: {matched_text[:120]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Essential logging requirements
        self._logger.warning(f"ATTENDANCE DETECTED AT {timestamp} FOR {subject}!")
        self._logger.info(f"Triggering notifications: {message}")

        # 1. Desktop Toast Notification
        if self._config.get("desktop", True):
            threading.Thread(
                target=self._show_toast,
                args=(title, message),
                daemon=True,
                name="ToastNotifierThread",
            ).start()

        # 2. MessageBox Popup (grabs visual focus)
        if self._config.get("popup", True):
            threading.Thread(
                target=self._show_popup,
                args=(title, message),
                daemon=True,
                name="PopupNotifierThread",
            ).start()

        # 3. Audio Alarm
        if self._config.get("sound", True):
            threading.Thread(
                target=self._play_alarm,
                daemon=True,
                name="AudioAlarmThread",
            ).start()

        # 4. Discord Webhook Notification
        webhook_url = self._config.get("discord_webhook", "").strip()
        if webhook_url:
            threading.Thread(
                target=self._send_discord_webhook,
                args=(webhook_url, subject, matched_text),
                daemon=True,
                name="DiscordNotifierThread",
            ).start()

    def _show_toast(self, title: str, message: str) -> None:
        """Display a native Windows toast notification using winotify."""
        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id="Meet Attendance Bot",
                title=title,
                msg=message,
                duration="long",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception as exc:
            self._logger.error(f"Failed to display Windows toast notification: {exc}")

    def _show_popup(self, title: str, message: str) -> None:
        """Display a blocking Windows MessageBox in a background thread."""
        try:
            # 0x40 = MB_ICONINFORMATION | MB_OK | MB_SYSTEMMODAL (brings to top and grabs focus)
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x00010000)
        except Exception as exc:
            self._logger.error(f"Failed to display MessageBox popup: {exc}")

    def _play_alarm(self) -> None:
        """Play sound alarm based on configuration."""
        duration = self._config.get("alarm_duration_seconds", 8)
        repeat = self._config.get("repeat_alarm", True)
        alarm_file = Path(self._alarm_path) if self._alarm_path else None

        try:
            if alarm_file and alarm_file.exists():
                self._play_file_alarm(alarm_file, duration, repeat)
            else:
                self._play_system_beep(duration, repeat)
        except Exception as exc:
            self._logger.error(f"Alarm playback failed: {exc}")

    def _play_file_alarm(self, path: Path, duration: int, repeat: bool) -> None:
        """Play WAV audio file using winsound."""
        import winsound
        from core.bot_state import state

        flags = winsound.SND_FILENAME | winsound.SND_ASYNC
        if repeat:
            flags |= winsound.SND_LOOP

        self._logger.info(f"Playing alarm file: {path.name}")
        winsound.PlaySound(str(path), flags)
        
        # Keep playing for the specified duration or until marked
        end_time = time.time() + duration
        while time.time() < end_time:
            if state.attendance_marked:
                break
            time.sleep(0.2)
        
        # Stop sound
        winsound.PlaySound(None, 0)
        self._logger.info("Alarm file playback finished.")

    def _play_system_beep(self, duration: int, repeat: bool) -> None:
        """Play fallback Windows system warning beeps."""
        import winsound
        from core.bot_state import state

        end_time = time.time() + duration
        self._logger.info("Playing system beep alarm...")
        
        while time.time() < end_time:
            if state.attendance_marked:
                break
            # Play exclamation sound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            # Sleep 1.5 seconds between repeated beeps
            for _ in range(15 if repeat else int(duration * 10)):
                if state.attendance_marked:
                    break
                time.sleep(0.1)
            if not repeat:
                break
        
        self._logger.info("System beep alarm finished.")

    def _send_discord_webhook(self, webhook_url: str, subject: str, matched_text: str) -> None:
        """Send attendance alert directly to a Discord Webhook (which pings your phone!)."""
        import urllib.request
        import json
        
        try:
            payload = {
                "content": (
                    f"🚨 **MEET ATTENDANCE DETECTED** 🚨\n"
                    f"**Class**: `{subject}`\n"
                    f"**Context**: *\"{matched_text.strip()}\"*\n"
                    f"*(Click 'Attendance Marked' on your dashboard to mute the alarm)*"
                )
            }
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Meet-Attendance-Bot/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status in (200, 204):
                    self._logger.info("Discord Webhook alert sent successfully.")
                else:
                    self._logger.warning(f"Discord Webhook returned status code: {response.status}")
        except Exception as exc:
            self._logger.error(f"Failed to send Discord Webhook notification: {exc}")
