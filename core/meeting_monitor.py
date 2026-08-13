"""In-meeting monitor: manages active pipeline, syncs transcripts/alerts, and handles overrides."""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Page

from core.attendance_detector import AttendanceDetector
from core.bot_state import state
from core.listener import TranscriptionListener
from core.logger import BotLogger
from core.notifier import Notifier
from core.recorder import AudioRecorder
from core.utils import MEETING_POLL_SECONDS


class MeetingMonitor:
    """Monitors the active meeting, records/transcribes audio, and pushes updates to GUI."""

    def __init__(
        self,
        config: dict[str, Any],
        logger: BotLogger,
        paths: dict[str, Path],
    ) -> None:
        self._config = config
        self._logger = logger
        self._paths = paths

        self._recorder: AudioRecorder | None = None
        self._listener: TranscriptionListener | None = None
        self._detector = AttendanceDetector(config, logger)
        self._notifier = Notifier(config, logger)

        self._transcript_lines: list[str] = []

    def run(self, page: Page, class_info: dict[str, Any], leave_at_dt: datetime) -> str:
        """Monitor the meeting until scheduled leave time, thread stop, or override.

        Returns one of: "completed", "stopped", "manual_leave", "disconnected".
        """
        subject = class_info["subject"]
        self._logger.info(
            f"Monitoring active class: {subject}. Auto-leave scheduled for: {leave_at_dt.strftime('%H:%M:%S')}"
        )
        state.status_text = f"Admitted — Monitoring: {subject}"

        on_transcript = self._build_transcript_handler(class_info)
        self._start_audio_pipeline(on_transcript)

        status = "completed"
        try:
            while True:
                # 1. UI Check: Was the bot stopped or leave commanded?
                if not state.bot_active:
                    self._logger.info("Bot stopped by user during monitoring.")
                    status = "stopped"
                    break
                if state.force_action == "leave_meeting":
                    state.force_action = None
                    self._logger.info("Manual 'Leave Meeting' override triggered.")
                    status = "manual_leave"
                    break

                now = datetime.now()
                if now >= leave_at_dt:
                    self._logger.info("Auto-leave time reached.")
                    status = "completed"
                    break

                if page.is_closed():
                    self._logger.warning("Browser tab was closed by the user.")
                    status = "disconnected"
                    break

                # Verify connection presence
                try:
                    leave_patterns = [
                        re.compile(r"leave call", re.I),
                        re.compile(r"leave meeting", re.I),
                        re.compile(r"\bleave\b", re.I),
                    ]
                    in_meeting = False
                    for pattern in leave_patterns:
                        locator = page.get_by_role("button", name=pattern)
                        if locator.count() > 0 and locator.first.is_visible():
                            in_meeting = True
                            break

                    if not in_meeting:
                        self._logger.warning(
                            "Could not find 'Leave' button. We might have disconnected or been kicked."
                        )
                        status = "disconnected"
                        break

                except Exception as exc:
                    self._logger.error(
                        f"Exception checking meeting status (tab may have crashed): {exc}"
                    )
                    status = "disconnected"
                    break

                remaining = int((leave_at_dt - now).total_seconds())
                state.status_text = f"Monitoring {subject} ({remaining // 60}m left)"
                
                # Sleep responsively in short increments
                for _ in range(MEETING_POLL_SECONDS):
                    if not state.bot_active:
                        break
                    if state.force_action == "leave_meeting":
                        break
                    time.sleep(1)

        finally:
            self._stop_audio_pipeline()
            self._save_transcript(class_info)

        return status

    def _build_transcript_handler(
        self,
        class_info: dict[str, Any],
    ) -> Callable[[str], None]:
        """Build the callback handler for real-time transcription segments, syncing with GUI."""
        def handle_transcript(text: str) -> None:
            clean_text = text.strip()
            if not clean_text:
                return

            timestamp = datetime.now().strftime("%H:%M:%S")
            line = f"[{timestamp}] {clean_text}"
            self._transcript_lines.append(line)
            
            # Send transcribed speech segment directly to GUI transcript_queue
            state.transcript_queue.put(line)
            
            self._logger.debug(f"Speech segment: {clean_text}")

            # Check keywords and alert (if not already marked)
            if not state.attendance_marked:
                if self._detector.check(clean_text):
                    # Send warning to GUI alert queue
                    state.alert_queue.put((class_info["subject"], clean_text))
                    self._notifier.alert_attendance(class_info["subject"], clean_text)

        return handle_transcript

    def _start_audio_pipeline(self, on_transcript: Callable[[str], None]) -> None:
        """Start the audio recording and transcription background processes."""
        recording_cfg = self._config["recording"]
        speech_cfg = self._config["speech"]

        if not recording_cfg.get("enabled", True):
            self._logger.warning("Audio recording is disabled in config.json.")
            return

        self._logger.info("Initializing loopback audio recorder...")
        self._recorder = AudioRecorder(
            chunk_dir=self._paths["chunks"],
            samplerate=recording_cfg.get("samplerate", 48_000),
            channels=recording_cfg.get("channels", 2),
            chunk_seconds=recording_cfg.get("chunk_seconds", 30),
            logger=self._logger,
        )

        if speech_cfg.get("enabled", True):
            self._logger.info("Initializing faster-whisper transcription listener...")
            self._listener = TranscriptionListener(
                config=self._config,
                on_transcript=on_transcript,
                logger=self._logger,
            )
            self._recorder.start(on_chunk=self._listener.process_chunk)
        else:
            self._recorder.start()

        self._logger.info("Audio recording pipeline started.")

    def _stop_audio_pipeline(self) -> None:
        """Stop all background recording and transcription workers."""
        if self._recorder is not None:
            self._logger.info("Stopping audio recorder...")
            self._recorder.stop()
            self._recorder = None

        if self._listener is not None:
            self._logger.info("Stopping transcription listener...")
            self._listener.stop()
            self._listener = None

    def _save_transcript(self, class_info: dict[str, Any]) -> None:
        """Save the accumulated session transcript lines to a text file."""
        if not self._config["speech"].get("save_transcript", True):
            return
        if not self._transcript_lines:
            self._logger.info("No audio transcribed during this session; skipping transcript file creation.")
            return

        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_subject = re.sub(r"[^\w\-]", "_", class_info["subject"])
        start_str = class_info["start"].replace(":", "")
        
        filename = f"{date_str}_{class_info['day']}_{safe_subject}_{start_str}.txt"
        path = self._paths["transcripts"] / filename

        try:
            path.write_text("\n".join(self._transcript_lines) + "\n", encoding="utf-8")
            self._logger.info(f"Transcript saved to: {path}")
        except Exception as exc:
            self._logger.error(f"Failed to write transcript file to disk: {exc}")
