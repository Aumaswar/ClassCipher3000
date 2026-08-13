"""Centred borderless startup splash screen with fade-in and slide-up animation and chime."""

from __future__ import annotations

import time
import threading
import customtkinter as ctk
from typing import Any, Callable

from ui.theme import Theme


class SplashScreen(ctk.CTkToplevel):
    """Bespoke borderless startup splash screen with slide-up fade animations."""

    def __init__(self, parent: Any, on_complete: Callable[[], None]) -> None:
        super().__init__(parent)
        self.on_complete = on_complete

        # Hide OS window frame
        self.overrideredirect(True)
        self.configure(fg_color=Theme.BG_DARK)

        # Force system to update idle window tasks to get accurate screen dimensions
        self.update_idletasks()

        # Set size and coordinates
        self.width = 460
        self.height = 240
        
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        self.x = (self.screen_width - self.width) // 2
        self.y_target = (self.screen_height - self.height) // 2
        self.y_start = self.y_target + 30  # Start slightly lower
        
        # Start hidden and positioned at starting point
        self.attributes("-alpha", 0.0)
        self.geometry(f"{self.width}x{self.height}+{self.x}+{self.y_start}")

        # Configure layout grids
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # Title
        self.grid_rowconfigure(2, weight=0) # Author
        self.grid_rowconfigure(3, weight=1) # Spacer
        self.grid_columnconfigure(0, weight=1)

        # Title (AGY BOT)
        self.lbl_title = ctk.CTkLabel(
            self,
            text="AGY BOT",
            font=ctk.CTkFont(family="Inter", size=42, weight="bold"),
            text_color=Theme.PRIMARY,  # Spotify Green
        )
        self.lbl_title.grid(row=1, column=0, pady=(0, 2))

        # Author (Made by Aum Aswar)
        self.lbl_author = ctk.CTkLabel(
            self,
            text="Made by Aum Aswar",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        self.lbl_author.grid(row=2, column=0)

        # Always on top during animation
        self.attributes("-topmost", True)

        # Play startup cyber chiptune arpeggio in the background
        threading.Thread(target=self._play_chime, daemon=True).start()

        # Animation states
        self.animation_step = 0
        self.total_fade_steps = 25  # 25 frames * 20ms = 500ms transition
        self._fade_in_slide_up()

    def _play_chime(self) -> None:
        """Play a futuristic arpeggio chime startup sound."""
        import winsound
        try:
            # Cyber startup arpeggio (C-Major 7 chord sweep)
            notes = [523, 659, 784, 988, 1047]  # C5, E5, G5, B5, C6
            for note in notes:
                winsound.Beep(note, 90)
                time.sleep(0.01)
        except Exception:
            pass

    def _fade_in_slide_up(self) -> None:
        """Phase 1: Fade-in and slide up to target Y coordinate."""
        if self.animation_step >= self.total_fade_steps:
            # Completed fade-in, hold in position for 1.2s
            self.attributes("-alpha", 1.0)
            self.geometry(f"{self.width}x{self.height}+{self.x}+{self.y_target}")
            self.after(1200, self._start_fade_out)
            return

        # Calculate animation step progress
        progress = self.animation_step / self.total_fade_steps
        
        # Calculate current alpha and Y position (ease-out transition)
        alpha = progress
        current_y = int(self.y_start - (progress * 30))
        
        self.attributes("-alpha", alpha)
        self.geometry(f"{self.width}x{self.height}+{self.x}+{current_y}")
        
        self.animation_step += 1
        self.after(20, self._fade_in_slide_up)

    def _start_fade_out(self) -> None:
        """Phase 2: Initialize the fade-out slide-up animation."""
        self.animation_step = 0
        self.y_fade_out_start = self.y_target
        self._fade_out_slide_up()

    def _fade_out_slide_up(self) -> None:
        """Phase 3: Fade-out and continue sliding up (dissolve exit)."""
        if self.animation_step >= self.total_fade_steps:
            # Complete! Close splash and call completion handler
            self.destroy()
            self.on_complete()
            return

        # Calculate progress
        progress = self.animation_step / self.total_fade_steps
        
        # Fade out opacity and slide upwards
        alpha = 1.0 - progress
        current_y = int(self.y_fade_out_start - (progress * 30))
        
        self.attributes("-alpha", alpha)
        self.geometry(f"{self.width}x{self.height}+{self.x}+{current_y}")
        
        self.animation_step += 1
        self.after(20, self._fade_out_slide_up)
