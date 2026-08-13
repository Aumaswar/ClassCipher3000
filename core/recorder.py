"""Windows loopback audio recorder with continuous, gapless block recording."""

from __future__ import annotations

import threading
import time
import uuid
import warnings
from pathlib import Path
from typing import Callable

# Suppress harmless soundcard data discontinuity warnings from spamming the console
warnings.filterwarnings("ignore", message=".*data discontinuity in recording.*")

import numpy as np
import soundcard as sc
import soundfile as sf

from core.logger import BotLogger

ChunkCallback = Callable[[Path], None]


class AudioRecorder:
    """Record system audio in a background thread, saving 30-second chunks continuously."""

    def __init__(
        self,
        chunk_dir: Path,
        logger: BotLogger,
        samplerate: int = 48_000,
        channels: int = 2,
        chunk_seconds: int = 30,
    ) -> None:
        self._chunk_dir = chunk_dir
        self._logger = logger
        self._samplerate = samplerate
        self._channels = channels
        self._chunk_seconds = chunk_seconds

        self._recording = False
        self._thread: threading.Thread | None = None
        self._on_chunk: ChunkCallback | None = None

        self._chunk_dir.mkdir(parents=True, exist_ok=True)

    def start(self, on_chunk: ChunkCallback | None = None) -> None:
        """Start the background recording thread."""
        if self._recording:
            return

        self._on_chunk = on_chunk
        self._recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        self._logger.info("Audio recording thread started.")

    def stop(self) -> None:
        """Stop recording and wait for the thread to finish cleanly."""
        self._recording = False
        if self._thread is not None:
            # Join with timeout to avoid blocking main thread indefinitely
            self._thread.join(timeout=5)
            self._thread = None
        self._logger.info("Audio recording thread stopped.")

    def _record_loop(self) -> None:
        """Continuously capture audio in short blocks and accumulate into 5s chunks."""
        from core.bot_state import state
        mic = None
        accumulated_data: list[np.ndarray] = []
        block_size_seconds = 0.1
        frames_per_block = int(self._samplerate * block_size_seconds)

        try:
            while self._recording:
                # 1. Acquire loopback recording device
                if mic is None:
                    try:
                        speaker = sc.default_speaker()
                        mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
                        self._logger.info(f"Acquired loopback device for speaker: {speaker.name}")
                    except Exception as exc:
                        self._logger.error(f"Audio device unavailable, retrying in 5s: {exc}")
                        time.sleep(5)
                        continue

                # 2. Record a short block
                try:
                    # mic.record returns a float32 numpy array of shape (numframes, channels)
                    data = mic.record(
                        numframes=frames_per_block,
                        samplerate=self._samplerate,
                    )
                    accumulated_data.append(data)

                    # Update live audio peak in bot state for UI visualizer
                    if data is not None and data.size > 0:
                        state.audio_peak = float(np.max(np.abs(data)))
                    else:
                        state.audio_peak = 0.0

                    # Check if we have accumulated enough blocks for a full chunk
                    if len(accumulated_data) * block_size_seconds >= self._chunk_seconds:
                        chunk_data = np.concatenate(accumulated_data, axis=0)
                        accumulated_data.clear()

                        # Save and run callback asynchronously so we don't stall recording
                        threading.Thread(
                            target=self._save_chunk_and_dispatch,
                            args=(chunk_data,),
                            daemon=True,
                        ).start()

                except Exception as exc:
                    self._logger.error(f"Recording capture error (device might be lost): {exc}")
                    # Reset mic to force re-acquisition in next loop iteration
                    mic = None
                    state.audio_peak = 0.0
                    time.sleep(2)
        finally:
            state.audio_peak = 0.0

    def _save_chunk_and_dispatch(self, data: np.ndarray) -> None:
        """Save a wav file of the audio data and execute the chunk callback."""
        try:
            chunk_filename = f"chunk_{int(time.time())}_{uuid.uuid4().hex[:8]}.wav"
            chunk_path = self._chunk_dir / chunk_filename
            
            # soundfile.write handles numpy array writing directly
            sf.write(str(chunk_path), data, self._samplerate)
            self._logger.debug(f"Saved audio chunk file: {chunk_filename}")

            if self._on_chunk is not None:
                try:
                    self._on_chunk(chunk_path)
                except Exception as exc:
                    self._logger.error(f"Error in transcription chunk callback: {exc}")

        except Exception as exc:
            self._logger.error(f"Failed to write audio chunk file to disk: {exc}")
