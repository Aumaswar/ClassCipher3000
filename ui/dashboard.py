"""Main GUI Dashboard for Google Meet Attendance Bot using a premium dark theme."""

from __future__ import annotations

import queue
import threading
import time
import customtkinter as ctk
from datetime import datetime
from typing import Any

from core.bot_state import state
from core.config_manager import ConfigManager
from ui.theme import Theme
from ui.timetable_page import TimetablePage
from ui.settings_page import SettingsPage
from ui.monitor_page import MonitorPage

ctk.set_appearance_mode("dark")


class Dashboard(ctk.CTk):
    """Main CustomTkinter GUI Application with premium dark theme styling."""

    def __init__(self, config_manager: ConfigManager, bot_worker_func: Any) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.bot_worker_func = bot_worker_func
        self.bot_thread: threading.Thread | None = None

        self.title("Google Meet Attendance Bot Control Center")
        self.geometry("980x680")
        self.minimum_width = 850
        self.minimum_height = 580
        self.minsize(self.minimum_width, self.minimum_height)
        self.configure(fg_color=Theme.BG_DARK)

        # Set up window grid
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Content Area
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Navigation Panel
        self._build_sidebar()

        # 2. Main Content Container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Initialize sub-pages
        self.timetable_page = TimetablePage(self.content_frame, self.config_manager)
        self.settings_page = SettingsPage(self.content_frame, self.config_manager)
        self.monitor_page = MonitorPage(self.content_frame)

        # Build Home frame
        self._build_home_page()

        # Default page display
        self.select_page("home")

        # Start updater polling loop
        self._poll_queues()

        # Clean window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self) -> None:
        """Create the premium left-side navigation sidebar."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
            fg_color=Theme.SIDEBAR_BG,
            border_color=Theme.BORDER,
            border_width=1,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="AGY MEET BOT",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=Theme.PRIMARY,
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 25))

        # Navigation buttons
        self.nav_home = ctk.CTkButton(
            self.sidebar,
            text="Dashboard",
            anchor="w",
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.select_page("home"),
        )
        self.nav_home.grid(row=1, column=0, padx=15, pady=4, sticky="ew")

        self.nav_timetable = ctk.CTkButton(
            self.sidebar,
            text="Timetable",
            anchor="w",
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.select_page("timetable"),
        )
        self.nav_timetable.grid(row=2, column=0, padx=15, pady=4, sticky="ew")

        self.nav_settings = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            anchor="w",
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.select_page("settings"),
        )
        self.nav_settings.grid(row=3, column=0, padx=15, pady=4, sticky="ew")

        self.nav_monitor = ctk.CTkButton(
            self.sidebar,
            text="Live Monitor",
            anchor="w",
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.select_page("monitor"),
        )
        self.nav_monitor.grid(row=4, column=0, padx=15, pady=4, sticky="ew")

        self.version_lbl = ctk.CTkLabel(
            self.sidebar,
            text="Version 2.2.0",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color=Theme.TEXT_MUTED,
        )
        self.version_lbl.grid(row=6, column=0, padx=20, pady=(20, 2))

        self.author_lbl = ctk.CTkLabel(
            self.sidebar,
            text="Made by Aum Aswar",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=Theme.PRIMARY,
        )
        self.author_lbl.grid(row=7, column=0, padx=20, pady=(0, 20))

    def _build_home_page(self) -> None:
        """Create the Home dashboard panel."""
        self.home_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        self.home_frame.grid_rowconfigure(0, weight=0)  # Title
        self.home_frame.grid_rowconfigure(1, weight=1)  # Status Cards grid
        self.home_frame.grid_rowconfigure(2, weight=0)  # Controls
        self.home_frame.grid_columnconfigure(0, weight=1)

        # Title Header
        self.home_title = ctk.CTkLabel(
            self.home_frame,
            text="Control Dashboard",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=Theme.TEXT_MAIN,
        )
        self.home_title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Cards Grid
        cards_container = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        cards_container.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        cards_container.grid_columnconfigure(0, weight=1)
        cards_container.grid_columnconfigure(1, weight=1)
        cards_container.grid_rowconfigure(0, weight=1)
        cards_container.grid_rowconfigure(1, weight=1)

        # Card 1: Bot Engine State
        self.card_bot = self._create_card(cards_container, "Bot Engine Status", 0, 0)
        self.lbl_bot_status = ctk.CTkLabel(
            self.card_bot,
            text="STOPPED",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=Theme.DANGER,
        )
        self.lbl_bot_status.pack(expand=True, pady=(5, 15))

        # Card 2: Current Task Status
        self.card_status = self._create_card(cards_container, "Current Session Action", 0, 1)
        self.lbl_action_status = ctk.CTkLabel(
            self.card_status,
            text="Idle",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=Theme.WARNING,
            wraplength=300,
        )
        self.lbl_action_status.pack(expand=True, pady=(5, 15))

        # Modern Audio Visualizer VU Meter (encapsulated under current action)
        self.visualizer_frame = ctk.CTkFrame(self.card_status, fg_color="transparent")
        self.visualizer_frame.pack(side="bottom", fill="x", padx=15, pady=(5, 15))
        
        self.visualizer_lbl = ctk.CTkLabel(
            self.visualizer_frame,
            text="AUDIO LEVEL",
            font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        self.visualizer_lbl.pack(anchor="w", pady=(0, 2))

        self.audio_bar = ctk.CTkProgressBar(
            self.visualizer_frame,
            height=6,
            corner_radius=3,
            fg_color=Theme.BORDER,
            progress_color=Theme.SUCCESS,
        )
        self.audio_bar.pack(fill="x")
        self.audio_bar.set(0)

        # Card 3: Next Class Scheduled
        self.card_next = self._create_card(cards_container, "Next Scheduled Session", 1, 0)
        self.lbl_next_class = ctk.CTkLabel(
            self.card_next,
            text="None",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=Theme.TEXT_MAIN,
            wraplength=300,
        )
        self.lbl_next_class.pack(expand=True, pady=(5, 15))

        # Card 4: Early Join Countdown
        self.card_countdown = self._create_card(cards_container, "Wait Countdown", 1, 1)
        self.lbl_countdown = ctk.CTkLabel(
            self.card_countdown,
            text="N/A",
            font=ctk.CTkFont(family="Inter", size=26, weight="bold"),
            text_color=Theme.SECONDARY,
        )
        self.lbl_countdown.pack(expand=True, pady=(5, 15))

        # Actions Frame
        actions_frame = ctk.CTkFrame(
            self.home_frame,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=10,
        )
        actions_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")

        ctk.CTkLabel(
            actions_frame,
            text="Manual Operation Overrides",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=Theme.TEXT_MAIN,
        ).pack(side="top", anchor="w", padx=20, pady=(15, 5))

        # Row 1: Bot Runner controls
        row_runner = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row_runner.pack(side="top", fill="x", padx=10, pady=(5, 5))

        self.btn_start = ctk.CTkButton(
            row_runner,
            text="Start Bot",
            height=36,
            corner_radius=6,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            text_color=Theme.BG_DARK,
            text_color_disabled=Theme.TEXT_MUTED,
            font=ctk.CTkFont(weight="bold"),
            command=self._start_bot_thread,
        )
        self.btn_start.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.btn_stop = ctk.CTkButton(
            row_runner,
            text="Stop Bot",
            height=36,
            corner_radius=6,
            fg_color=Theme.BORDER,
            hover_color=Theme.DANGER_HOVER,
            text_color=Theme.TEXT_MAIN,
            text_color_disabled=Theme.TEXT_MUTED,
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self._stop_bot,
        )
        self.btn_stop.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        # Row 2: Live Meeting Overrides
        row_meeting = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row_meeting.pack(side="top", fill="x", padx=10, pady=(5, 15))

        self.btn_join = ctk.CTkButton(
            row_meeting,
            text="Join Now",
            height=36,
            corner_radius=6,
            fg_color=Theme.BORDER,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            text_color_disabled=Theme.TEXT_MUTED,
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self._force_join_now,
        )
        self.btn_join.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.btn_leave = ctk.CTkButton(
            row_meeting,
            text="Leave Meeting",
            height=36,
            corner_radius=6,
            fg_color=Theme.BORDER,
            hover_color=Theme.WARNING_HOVER,
            text_color=Theme.BG_DARK,
            text_color_disabled=Theme.TEXT_MUTED,
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self._force_leave_meeting,
        )
        self.btn_leave.pack(side="left", padx=10, pady=5, expand=True, fill="x")

        self.btn_marked = ctk.CTkButton(
            row_meeting,
            text="Attendance Marked",
            height=36,
            corner_radius=6,
            fg_color=Theme.BORDER,
            hover_color=Theme.PRIMARY_HOVER,
            text_color=Theme.BG_DARK,
            text_color_disabled=Theme.TEXT_MUTED,
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self._mark_attendance_done,
        )
        self.btn_marked.pack(side="left", padx=10, pady=5, expand=True, fill="x")

    def _create_card(self, parent: ctk.CTkFrame, title: str, row: int, col: int) -> ctk.CTkFrame:
        """Create a premium styled card container frame."""
        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            border_width=1,
            corner_radius=10,
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        lbl = ctk.CTkLabel(
            card,
            text=title.upper(),
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        lbl.pack(anchor="w", padx=15, pady=(12, 5))
        return card

    def select_page(self, page_name: str) -> None:
        """Switch navigation panel on sidebar click."""
        # Reset navigation button styles
        for btn in (self.nav_home, self.nav_timetable, self.nav_settings, self.nav_monitor):
            btn.configure(
                fg_color="transparent",
                text_color=Theme.TEXT_MUTED,
            )

        # Hide all pages
        self.home_frame.grid_forget()
        self.timetable_page.grid_forget()
        self.settings_page.grid_forget()
        self.monitor_page.grid_forget()

        # Display selection
        if page_name == "home":
            self.nav_home.configure(fg_color=Theme.PRIMARY, text_color=Theme.BG_DARK)
            self.home_frame.grid(row=0, column=0, sticky="nsew")
        elif page_name == "timetable":
            self.timetable_page.classes = self.config_manager.get_config().get("classes", [])
            self.timetable_page._render_rows()
            self.nav_timetable.configure(fg_color=Theme.PRIMARY, text_color=Theme.BG_DARK)
            self.timetable_page.grid(row=0, column=0, sticky="nsew")
        elif page_name == "settings":
            self.nav_settings.configure(fg_color=Theme.PRIMARY, text_color=Theme.BG_DARK)
            self.settings_page.grid(row=0, column=0, sticky="nsew")
        elif page_name == "monitor":
            self.nav_monitor.configure(fg_color=Theme.PRIMARY, text_color=Theme.BG_DARK)
            self.monitor_page.grid(row=0, column=0, sticky="nsew")

    def _start_bot_thread(self) -> None:
        if state.bot_active:
            return

        state.bot_active = True
        self.lbl_bot_status.configure(text="RUNNING", text_color=Theme.SUCCESS)
        self.btn_start.configure(state="disabled", fg_color=Theme.BORDER)
        self.btn_stop.configure(state="normal", fg_color=Theme.DANGER)
        self.btn_join.configure(state="normal", fg_color=Theme.SECONDARY)

        # Start background thread
        self.bot_thread = threading.Thread(
            target=self.bot_worker_func,
            args=(self.config_manager,),
            daemon=True,
            name="BotRunnerDaemon",
        )
        self.bot_thread.start()
        self.monitor_page.append_log("Bot runner thread started by user.")

    def _stop_bot(self) -> None:
        if not state.bot_active:
            return

        state.bot_active = False
        state.force_action = "stop"
        self.monitor_page.append_log("Stop Bot command triggered. Closing browser...")

        self.lbl_bot_status.configure(text="STOPPED", text_color=Theme.DANGER)
        self.btn_start.configure(state="normal", fg_color=Theme.SUCCESS)
        self.btn_stop.configure(state="disabled", fg_color=Theme.BORDER)
        self.btn_join.configure(state="disabled", fg_color=Theme.BORDER)
        self.btn_leave.configure(state="disabled", fg_color=Theme.BORDER)

    def _force_join_now(self) -> None:
        state.force_action = "join_now"
        self.monitor_page.append_log("Manual 'Join Now' override requested.")

    def _force_leave_meeting(self) -> None:
        state.force_action = "leave_meeting"
        self.monitor_page.append_log("Manual 'Leave Meeting' command requested.")

    def _mark_attendance_done(self) -> None:
        import winsound
        state.attendance_marked = True
        try:
            winsound.PlaySound(None, 0)
        except Exception:
            pass
        self.monitor_page.append_log("User marked attendance as completed. Silencing alarm and muting alerts for this session.")
        self.btn_marked.configure(state="disabled", text="Attendance OK", fg_color=Theme.BORDER)

    def _poll_queues(self) -> None:
        # Retrieve logs
        try:
            while True:
                msg = state.log_queue.get_nowait()
                self.monitor_page.append_log(msg)
        except queue.Empty:
            pass

        # Retrieve transcripts
        try:
            while True:
                msg = state.transcript_queue.get_nowait()
                self.monitor_page.append_transcript(msg)
        except queue.Empty:
            pass

        # Retrieve alerts
        try:
            while True:
                subject, msg = state.alert_queue.get_nowait()
                self.monitor_page.append_alert(subject, msg)
        except queue.Empty:
            pass

        # Update dashboard state
        self.lbl_action_status.configure(text=state.status_text)
        self.lbl_countdown.configure(text=state.countdown_text)
        self.lbl_next_class.configure(text=state.current_class_label)

        # Smooth decay filter (VU meter style) for real-time loopback peak level
        current_val = self.audio_bar.get()
        target_val = state.audio_peak if state.active_page is not None else 0.0
        
        if target_val > current_val:
            # Quick attack
            new_val = target_val
        else:
            # Smooth exponential decay
            new_val = current_val - 0.25 * (current_val - target_val)
            
        self.audio_bar.set(max(0.0, min(1.0, new_val)))

        # Style activity status color coding
        if state.status_text == "Stopped":
            self.lbl_action_status.configure(text_color=Theme.DANGER)
        elif "Admitted" in state.status_text or "In Meeting" in state.status_text or "Monitoring" in state.status_text:
            self.lbl_action_status.configure(text_color=Theme.SUCCESS)
            self.btn_leave.configure(state="normal")
        else:
            self.lbl_action_status.configure(text_color=Theme.WARNING)

        # Enable/Disable buttons based on active page status
        if state.active_page is None or state.active_page.is_closed():
            self.btn_leave.configure(state="disabled", fg_color=Theme.BORDER)
            self.btn_marked.configure(state="disabled", text="Attendance Marked", fg_color=Theme.BORDER)
        else:
            self.btn_leave.configure(state="normal", fg_color=Theme.WARNING)
            if state.attendance_marked:
                self.btn_marked.configure(state="disabled", text="Attendance OK", fg_color=Theme.BORDER)
            else:
                self.btn_marked.configure(state="normal", text="Attendance Marked", fg_color=Theme.PRIMARY)

        self.after(100, self._poll_queues)

    def _on_close(self) -> None:
        """Clean closure sequence when closing window frame, waiting for background thread exit."""
        self._stop_bot()
        self.title("Closing... Releasing browser resources...")
        
        # Wait up to 4 seconds for the bot worker thread to cleanly stop Playwright
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=4.0)
            
        self.destroy()
