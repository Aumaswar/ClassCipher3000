"""Centred borderless startup splash screen with loading bar animation."""

from __future__ import annotations

import random
import customtkinter as ctk
from typing import Any, Callable

from ui.theme import Theme


class SplashScreen(ctk.CTkToplevel):
    """Bespoke borderless startup splash screen with loading bar animation."""

    def __init__(self, parent: Any, on_complete: Callable[[], None]) -> None:
        super().__init__(parent)
        self.on_complete = on_complete

        # Hide title bar (borderless window)
        self.overrideredirect(True)
        self.configure(fg_color=Theme.BG_DARK)

        # Set size and position in the center of the screen
        width = 460
        height = 240
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Configure layout grids
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # Title
        self.grid_rowconfigure(2, weight=0) # Author
        self.grid_rowconfigure(3, weight=0) # Progress
        self.grid_rowconfigure(4, weight=1) # Bottom spacer
        self.grid_columnconfigure(0, weight=1)

        # Title (AGY BOT)
        self.lbl_title = ctk.CTkLabel(
            self,
            text="AGY BOT",
            font=ctk.CTkFont(family="Inter", size=38, weight="bold"),
            text_color=Theme.PRIMARY,  # Spotify Green
        )
        self.lbl_title.grid(row=1, column=0, pady=(0, 5))

        # Author (Made by Aum Aswar)
        self.lbl_author = ctk.CTkLabel(
            self,
            text="Made by Aum Aswar",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        self.lbl_author.grid(row=2, column=0, pady=(0, 25))

        # Animated Progress Bar
        self.progress = ctk.CTkProgressBar(
            self,
            width=300,
            height=4,
            corner_radius=2,
            fg_color=Theme.BORDER,
            progress_color=Theme.PRIMARY,  # Spotify Green
        )
        self.progress.grid(row=3, column=0)
        self.progress.set(0.0)

        # Always on top during loading
        self.attributes("-topmost", True)

        # Start animation loop
        self.progress_val = 0.0
        self._animate_progress()

    def _animate_progress(self) -> None:
        """Increment progress bar smoothly until it hits 1.0, then close splash."""
        if self.progress_val >= 1.0:
            self.destroy()
            self.on_complete()
            return

        # Increment value with a bit of random variation for a natural loading feel
        self.progress_val += random.uniform(0.015, 0.035)
        if self.progress_val > 1.0:
            self.progress_val = 1.0
            
        self.progress.set(self.progress_val)
        
        # Trigger next frame in a random millisecond delay for human-made loading effect
        delay = random.randint(15, 35)
        self.after(delay, self._animate_progress)
