"""Real-time audio chunk transcription using Faster-Whisper."""

from __future__ import annotations

import threading
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable

from core.logger import BotLogger


class TranscriptionListener:
    """Asynchronously transcribes audio chunks from a queue using Faster-Whisper."""

    # Class-level cache to share model instance across active class sessions
    _cached_model: Any = None
    _cached_model_size: str | None = None

    def __init__(
        self,
        config: dict[str, Any],
        logger: BotLogger,
        on_transcript: Callable[[str], None],
    ) -> None:
        self._config = config
        self._logger = logger
        self._on_transcript = on_transcript
        self._speech = config["speech"]

        self._queue: Queue[Path] = Queue()
        self._running = False
        self._thread: threading.Thread | None = None
        self._model = None
        self._model_lock = threading.Lock()

    def process_chunk(self, chunk_path: Path) -> None:
        """Enqueue an audio chunk file for background transcription."""
        self._ensure_worker()
        self._queue.put(chunk_path)

    def _ensure_worker(self) -> None:
        """Ensure the transcription worker thread is active."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        self._logger.info("Transcription listener worker thread started.")

    def _load_model(self) -> None:
        """Initialize the WhisperModel, falling back from CUDA to CPU if necessary."""
        if self._model is not None:
            return

        model_size = self._speech.get("model", "base")
        device_config = self._speech.get("device", "auto").strip().lower()

        with self._model_lock:
            # Check if model is already loaded and cached at class-level
            if (TranscriptionListener._cached_model is not None and 
                TranscriptionListener._cached_model_size == model_size):
                self._model = TranscriptionListener._cached_model
                self._logger.info(f"Reusing cached Whisper model '{model_size}' from previous session.")
                return

            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                self._logger.error("Could not import faster-whisper. Please check requirements.txt.")
                raise exc

            # 1. Attempt CUDA if requested or set to auto
            if device_config in ("cuda", "auto"):
                try:
                    self._logger.info(f"Attempting to load Whisper model '{model_size}' on CUDA...")
                    # float16 is standard for CUDA execution
                    model_inst = WhisperModel(model_size, device="cuda", compute_type="float16")
                    
                    # Run a dummy transcription to verify CUDA library availability (detects missing DLLs early)
                    import numpy as np
                    dummy_audio = np.zeros(100, dtype=np.float32)
                    list(model_inst.transcribe(dummy_audio))
                    
                    self._model = model_inst
                    TranscriptionListener._cached_model = model_inst
                    TranscriptionListener._cached_model_size = model_size
                    self._logger.info("Whisper model loaded and verified successfully on CUDA.")
                    return
                except Exception as exc:
                    self._logger.warning(
                        f"Failed to verify Whisper on CUDA (e.g. missing DLLs): {exc}. Falling back to CPU..."
                    )

            # 2. Fall back to CPU
            try:
                self._logger.info(f"Loading Whisper model '{model_size}' on CPU...")
                # int8 is standard for CPU execution to speed up inference
                model_inst = WhisperModel(model_size, device="cpu", compute_type="int8")
                
                self._model = model_inst
                TranscriptionListener._cached_model = model_inst
                TranscriptionListener._cached_model_size = model_size
                self._logger.info("Whisper model loaded successfully on CPU.")
            except Exception as exc:
                self._logger.error(f"Failed to load Whisper model on CPU: {exc}")
                raise exc

    def _worker_loop(self) -> None:
        """Process chunk queue and transcribe in a loop."""
        try:
            self._load_model()
        except Exception as exc:
            self._logger.error(f"Disabling speech transcription worker: {exc}")
            self._running = False
            return

        while self._running:
            try:
                chunk_path = self._queue.get(timeout=1.0)
            except Empty:
                continue

            try:
                if chunk_path.exists():
                    text = self._transcribe(chunk_path)
                    if text:
                        self._on_transcript(text)
            except Exception as exc:
                self._logger.error(f"Transcription failed for chunk {chunk_path.name}: {exc}")
            finally:
                self._cleanup_chunk(chunk_path)

    def _transcribe(self, chunk_path: Path) -> str:
        """Run Whisper transcription on the specified audio file, falling back to CPU if CUDA fails."""
        if self._model is None:
            return ""

        try:
            lang = self._speech.get("language", "en")
            lang_param = None if lang.lower().strip() == "auto" else lang

            segments, _info = self._model.transcribe(
                str(chunk_path),
                language=lang_param,
                beam_size=self._speech.get("beam_size", 5),
                vad_filter=self._speech.get("vad_filter", True),
            )
            # Force generator consumption to catch lazy-load library errors
            parts = [segment.text.strip() for segment in segments if segment.text.strip()]
            return " ".join(parts)
        except Exception as exc:
            exc_str = str(exc).lower()
            if "cublas" in exc_str or "cudnn" in exc_str or "cuda" in exc_str:
                self._logger.warning(
                    f"CUDA execution failed during transcription: {exc}. "
                    f"Automatically falling back to CPU for future chunks..."
                )
                with self._model_lock:
                    self._model = None
                    try:
                        model_size = self._speech.get("model", "base")
                        from faster_whisper import WhisperModel
                        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")
                        self._logger.info("Whisper model reloaded successfully on CPU.")
                        
                        # Re-attempt transcription on CPU
                        segments, _info = self._model.transcribe(
                            str(chunk_path),
                            language=lang_param,
                            beam_size=self._speech.get("beam_size", 5),
                            vad_filter=self._speech.get("vad_filter", True),
                        )
                        parts = [segment.text.strip() for segment in segments if segment.text.strip()]
                        return " ".join(parts)
                    except Exception as fallback_exc:
                        self._logger.error(f"CPU fallback transcription failed: {fallback_exc}")
                        raise fallback_exc
            else:
                raise exc

    def _cleanup_chunk(self, chunk_path: Path) -> None:
        """Delete the temporary audio chunk file from disk."""
        try:
            chunk_path.unlink(missing_ok=True)
        except Exception as exc:
            self._logger.debug(f"Could not delete temporary chunk file {chunk_path.name}: {exc}")

    def stop(self) -> None:
        """Stop the background worker thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None
        self._logger.info("Transcription listener worker thread stopped.")
