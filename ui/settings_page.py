"""Settings page for Google Meet Attendance Bot with premium dark theme."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog
from typing import Any

from core.config_manager import ConfigManager
from ui.theme import Theme


class SettingsPage(ctk.CTkFrame):
    """GUI Page displaying and allowing editing of bot configuration parameters."""

    def __init__(self, parent: Any, config_manager: ConfigManager) -> None:
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager
        self.config = self.config_manager.get_config()

        # Grid config
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Title Label
        self.title_lbl = ctk.CTkLabel(
            self,
            text="Application Settings",
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            text_color=Theme.TEXT_MAIN,
        )
        self.title_lbl.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Scrollable panel
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=2)

        self._build_user_card()
        self._build_meeting_card()
        self._build_speech_card()
        self._build_recording_card()
        self._build_notifications_card()
        
        # Save Button
        self.save_btn = ctk.CTkButton(
            self.scroll_frame,
            text="Save Settings",
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            text_color=Theme.BG_DARK,
            height=40,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            command=self._save_settings,
        )
        self.save_btn.grid(row=99, column=0, columnspan=2, padx=15, pady=30, sticky="ew")

    def _create_entry(self, row: int, initial_text: str) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            self.scroll_frame,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
            corner_radius=6,
        )
        entry.grid(row=row, column=1, padx=15, pady=6, sticky="ew")
        entry.insert(0, initial_text)
        return entry

    def _create_lbl(self, text: str, row: int) -> None:
        lbl = ctk.CTkLabel(
            self.scroll_frame,
            text=text,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        lbl.grid(row=row, column=0, padx=15, pady=6, sticky="e")

    def _build_user_card(self) -> None:
        self._add_section_header("User Setup Details", row=0)

        # Name
        self._create_lbl("User Configured Name:", 1)
        self.user_name_entry = self._create_entry(1, self.config["user"].get("name", ""))

        # Profile path
        self._create_lbl("Chrome Profile Path:", 2)
        prof_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        prof_frame.grid(row=2, column=1, padx=15, pady=6, sticky="ew")
        prof_frame.grid_columnconfigure(0, weight=1)
        prof_frame.grid_columnconfigure(1, weight=0)

        self.profile_entry = ctk.CTkEntry(
            prof_frame,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
            corner_radius=6,
        )
        self.profile_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.profile_entry.insert(0, self.config["browser"].get("persistent_profile", ""))

        self.profile_browse_btn = ctk.CTkButton(
            prof_frame,
            text="Browse",
            width=70,
            fg_color=Theme.CARD_HOVER,
            hover_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._browse_dir(self.profile_entry),
        )
        self.profile_browse_btn.grid(row=0, column=1, sticky="e")

    def _build_meeting_card(self) -> None:
        self._add_section_header("Mute & Wait Delays", row=3)

        # Early Minutes
        self._create_lbl("Join Early (Minutes):", 4)
        self.join_early_entry = self._create_entry(4, str(self.config["meeting"].get("join_early_minutes", 5)))

        # Late Minutes
        self._create_lbl("Leave Delay (Minutes):", 5)
        self.leave_late_entry = self._create_entry(5, str(self.config["meeting"].get("leave_late_minutes", 5)))

    def _build_speech_card(self) -> None:
        self._add_section_header("Speech Analysis & Keywords", row=6)

        # Keywords
        self._create_lbl("Alert Keywords:", 7)
        self.keywords_entry = self._create_entry(7, ", ".join(self.config["attendance"].get("keywords", [])))

        # Whisper Model
        self._create_lbl("Faster-Whisper Model:", 8)
        self.whisper_model_combo = ctk.CTkComboBox(
            self.scroll_frame,
            values=["tiny", "base", "small", "medium", "large-v3"],
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            button_color=Theme.CARD_HOVER,
            button_hover_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
        )
        self.whisper_model_combo.grid(row=8, column=1, padx=15, pady=6, sticky="ew")
        self.whisper_model_combo.set(self.config["speech"].get("model", "base"))

        # Device
        self._create_lbl("Hardware Device:", 9)
        self.device_combo = ctk.CTkComboBox(
            self.scroll_frame,
            values=["auto", "cpu", "cuda"],
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            button_color=Theme.CARD_HOVER,
            button_hover_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
        )
        self.device_combo.grid(row=9, column=1, padx=15, pady=6, sticky="ew")
        self.device_combo.set(self.config["speech"].get("device", "auto"))

    def _build_recording_card(self) -> None:
        self._add_section_header("Audio Capture Folders", row=10)

        # Recordings folder
        self._create_lbl("Recordings Folder:", 11)
        rec_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        rec_frame.grid(row=11, column=1, padx=15, pady=6, sticky="ew")
        rec_frame.grid_columnconfigure(0, weight=1)
        rec_frame.grid_columnconfigure(1, weight=0)

        self.recordings_entry = ctk.CTkEntry(
            rec_frame,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
            corner_radius=6,
        )
        self.recordings_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.recordings_entry.insert(0, self.config["recording"].get("directory", ""))

        self.rec_browse_btn = ctk.CTkButton(
            rec_frame,
            text="Browse",
            width=70,
            fg_color=Theme.CARD_HOVER,
            hover_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self._browse_dir(self.recordings_entry),
        )
        self.rec_browse_btn.grid(row=0, column=1, sticky="e")

    def _build_notifications_card(self) -> None:
        self._add_section_header("Discord Phone Notifications", row=12)

        # Discord Webhook
        self._create_lbl("Discord Webhook URL:", 13)
        self.webhook_entry = self._create_entry(13, self.config["notifications"].get("discord_webhook", ""))

    def _add_section_header(self, title: str, row: int) -> None:
        lbl = ctk.CTkLabel(
            self.scroll_frame,
            text=title.upper(),
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=Theme.PRIMARY,
        )
        lbl.grid(row=row, column=0, columnspan=2, padx=15, pady=(20, 10), sticky="w")

    def _browse_dir(self, entry_widget: ctk.CTkEntry) -> None:
        folder = filedialog.askdirectory(initialdir=".")
        if folder:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, folder)

    def _save_settings(self) -> None:
        config = self.config_manager.get_config()

        # Update values
        config["user"]["name"] = self.user_name_entry.get().strip()
        config["browser"]["persistent_profile"] = self.profile_entry.get().strip()

        try:
            config["meeting"]["join_early_minutes"] = int(self.join_early_entry.get().strip())
        except ValueError:
            pass

        try:
            config["meeting"]["leave_late_minutes"] = int(self.leave_late_entry.get().strip())
        except ValueError:
            pass

        raw_kw = self.keywords_entry.get().strip()
        keywords_list = [kw.strip() for kw in raw_kw.split(",") if kw.strip()]
        config["attendance"]["keywords"] = keywords_list

        config["speech"]["model"] = self.whisper_model_combo.get()
        config["speech"]["device"] = self.device_combo.get()
        config["recording"]["directory"] = self.recordings_entry.get().strip()
        config["notifications"]["discord_webhook"] = self.webhook_entry.get().strip()

        self.config_manager.save_config(config)

        # Notify save complete
        old_text = self.title_lbl.cget("text")
        self.title_lbl.configure(text="Settings Saved Successfully!", text_color=Theme.SUCCESS)
        self.after(2000, lambda: self.title_lbl.configure(text=old_text, text_color=Theme.TEXT_MAIN))
