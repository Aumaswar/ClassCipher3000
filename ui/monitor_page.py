"""Real-time monitoring page for Google Meet Attendance Bot with premium dark theme."""

from __future__ import annotations

import os
import customtkinter as ctk
from datetime import datetime
from typing import Any

from ui.theme import Theme
from core.bot_state import state


class MonitorPage(ctk.CTkFrame):
    """GUI Page displaying real-time speech transcription, logs, and attendance alerts."""

    def __init__(self, parent: Any) -> None:
        super().__init__(parent, fg_color="transparent")

        # Layout grids
        self.grid_rowconfigure(0, weight=3)  # Top half (Transcript & Alerts)
        self.grid_rowconfigure(1, weight=2)  # Bottom half (Logs)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # 1. Transcript Panel (Top Left)
        self.trans_frame = ctk.CTkFrame(
            self,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=10,
        )
        self.trans_frame.grid(row=0, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.trans_frame.grid_rowconfigure(1, weight=1)
        self.trans_frame.grid_columnconfigure(0, weight=1)

        self.trans_lbl = ctk.CTkLabel(
            self.trans_frame,
            text="LIVE SPEECH TRANSCRIPT",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=Theme.PRIMARY,
        )
        self.trans_lbl.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")

        self.btn_bookmark = ctk.CTkButton(
            self.trans_frame,
            text="⭐ Bookmark Note",
            width=120,
            height=26,
            corner_radius=6,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            command=self._bookmark_highlight,
        )
        self.btn_bookmark.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="e")

        self.trans_box = ctk.CTkTextbox(
            self.trans_frame,
            fg_color=Theme.BG_DARK,
            text_color=Theme.TEXT_MAIN,
            border_color=Theme.BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.trans_box.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.trans_box.configure(state="disabled")

        # 2. Alerts Panel (Top/Bottom Right span)
        self.alert_frame = ctk.CTkFrame(
            self,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=10,
        )
        self.alert_frame.grid(row=0, column=1, rowspan=2, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.alert_frame.grid_rowconfigure(1, weight=1)
        self.alert_frame.grid_columnconfigure(0, weight=1)

        self.alert_lbl = ctk.CTkLabel(
            self.alert_frame,
            text="ATTENDANCE ALERTS",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=Theme.DANGER,
        )
        self.alert_lbl.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")

        self.alert_box = ctk.CTkTextbox(
            self.alert_frame,
            fg_color=Theme.BG_DARK,
            text_color=Theme.DANGER,
            border_color=Theme.BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.alert_box.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.alert_box.configure(state="disabled")

        # 3. Logs Panel (Bottom Left)
        self.log_frame = ctk.CTkFrame(
            self,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=10,
        )
        self.log_frame.grid(row=1, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew")
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_lbl = ctk.CTkLabel(
            self.log_frame,
            text="BOT ACTIVITY LOGS",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=Theme.SUCCESS,
        )
        self.log_lbl.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")

        self.log_box = ctk.CTkTextbox(
            self.log_frame,
            fg_color=Theme.BG_DARK,
            text_color=Theme.TEXT_MUTED,
            border_color=Theme.BORDER,
            border_width=1,
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.log_box.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.log_box.configure(state="disabled")

    def append_log(self, text: str) -> None:
        """Append log line to the Activity Log textbox."""
        self._append_text(self.log_box, text)

    def append_transcript(self, text: str) -> None:
        """Append transcribed speech segment to Transcript textbox."""
        self._append_text(self.trans_box, text)

    def append_alert(self, subject: str, text: str) -> None:
        """Display an attendance keyword detection warning card/text."""
        time_str = datetime.now().strftime("%H:%M:%S")
        alert_msg = f"[{time_str}] ALERT | {subject}:\n-> '{text.strip()}'\n" + "-" * 32 + "\n"
        self._append_text(self.alert_box, alert_msg)

    def _append_text(self, text_widget: ctk.CTkTextbox, text: str) -> None:
        """Write text to a CTkTextbox thread-safely and scroll to end."""
        text_widget.configure(state="normal")
        text_widget.insert("end", text + "\n")
        text_widget.configure(state="disabled")
        text_widget.see("end")

    def _bookmark_highlight(self) -> None:
        """Grab the last few lines of the transcript and append them to a notes file."""
        all_text = self.trans_box.get("1.0", "end-1c").strip()
        if not all_text:
            return

        lines = [line.strip() for line in all_text.split("\n") if line.strip()]
        if not lines:
            return

        # Grab last 5 lines for context
        snippet = "\n".join(lines[-5:])
        
        os.makedirs("notes", exist_ok=True)
        filename = f"notes/highlights_{datetime.now().strftime('%Y-%m-%d')}.txt"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        class_name = state.current_class_label if state.current_class_label else "No Active Class"
        
        entry = (
            f"=== LECTURE SNAPSHOT AT {timestamp} ({class_name}) ===\n"
            f"{snippet}\n"
            f"================================================\n\n"
        )
        
        with open(filename, "a", encoding="utf-8") as f:
            f.write(entry)

        # Notify the user via alerts box
        self.append_alert(
            "BOOKMARK SAVED", 
            f"Saved last 5 lines of translation to:\n{filename}"
        )
