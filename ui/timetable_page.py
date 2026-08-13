"""Timetable management page for Google Meet Attendance Bot with premium dark theme."""

from __future__ import annotations

import webbrowser
import customtkinter as ctk
from typing import Any, Callable

from core.config_manager import ConfigManager
from ui.theme import Theme


class ClassDialog(ctk.CTkToplevel):
    """Modal dialog to add or edit class details, premium styled."""

    def __init__(
        self,
        parent: Any,
        title: str,
        on_save: Callable[[dict[str, Any]], None],
        initial_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("450x460")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_DARK)
        
        self.transient(parent)
        self.grab_set()

        self.on_save = on_save
        self.initial_data = initial_data or {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        # Title/Header
        self.header_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color=Theme.PRIMARY,
        )
        self.header_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="w")

        # Helper method for labels
        def create_lbl(text: str, row: int):
            lbl = ctk.CTkLabel(
                self,
                text=text,
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=Theme.TEXT_MUTED,
            )
            lbl.grid(row=row, column=0, padx=20, pady=10, sticky="e")

        # Subject
        create_lbl("Subject Name:", 1)
        self.subject_entry = ctk.CTkEntry(
            self, placeholder_text="e.g. INS", fg_color=Theme.CARD_BG, border_color=Theme.BORDER
        )
        self.subject_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        if "subject" in self.initial_data:
            self.subject_entry.insert(0, self.initial_data["subject"])

        # Day
        create_lbl("Day of Week:", 2)
        self.day_combo = ctk.CTkComboBox(
            self,
            values=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            fg_color=Theme.CARD_BG,
            border_color=Theme.BORDER,
            button_color=Theme.CARD_HOVER,
            button_hover_color=Theme.BORDER,
        )
        self.day_combo.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        if "day" in self.initial_data:
            self.day_combo.set(self.initial_data["day"])

        # Start Time
        create_lbl("Start (HH:MM):", 3)
        self.start_entry = ctk.CTkEntry(
            self, placeholder_text="e.g. 09:30", fg_color=Theme.CARD_BG, border_color=Theme.BORDER
        )
        self.start_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        if "start" in self.initial_data:
            self.start_entry.insert(0, self.initial_data["start"])

        # End Time
        create_lbl("End (HH:MM):", 4)
        self.end_entry = ctk.CTkEntry(
            self, placeholder_text="e.g. 10:25", fg_color=Theme.CARD_BG, border_color=Theme.BORDER
        )
        self.end_entry.grid(row=4, column=1, padx=20, pady=10, sticky="ew")
        if "end" in self.initial_data:
            self.end_entry.insert(0, self.initial_data["end"])

        # Meet Link
        create_lbl("Meet Link:", 5)
        self.link_entry = ctk.CTkEntry(
            self, placeholder_text="meet.google.com/xxx-xxxx-xxx", fg_color=Theme.CARD_BG, border_color=Theme.BORDER
        )
        self.link_entry.grid(row=5, column=1, padx=20, pady=10, sticky="ew")
        if "link" in self.initial_data:
            self.link_entry.insert(0, self.initial_data["link"])

        # Actions
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, columnspan=2, padx=20, pady=25, sticky="ew")
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)

        self.save_btn = ctk.CTkButton(
            self.btn_frame,
            text="Save",
            height=32,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            text_color=Theme.BG_DARK,
            font=ctk.CTkFont(weight="bold"),
            command=self._save,
        )
        self.save_btn.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="Cancel",
            height=32,
            fg_color=Theme.CARD_HOVER,
            hover_color=Theme.BORDER,
            text_color=Theme.TEXT_MAIN,
            font=ctk.CTkFont(weight="bold"),
            command=self.destroy,
        )
        self.cancel_btn.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

    def _save(self) -> None:
        subject = self.subject_entry.get().strip()
        day = self.day_combo.get()
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        link = self.link_entry.get().strip()

        if not subject or not start or not end or not link:
            self.header_label.configure(
                text="Please fill in all fields!",
                text_color=Theme.DANGER,
            )
            return

        result = {
            "subject": subject,
            "day": day,
            "start": start,
            "end": end,
            "link": link,
            "enabled": self.initial_data.get("enabled", True),
        }
        self.on_save(result)
        self.destroy()


class TimetablePage(ctk.CTkFrame):
    """Scrollable class sessions list editor with premium dark design."""

    def __init__(self, parent: Any, config_manager: ConfigManager) -> None:
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager
        self.classes: list[dict[str, Any]] = self.config_manager.get_config().get("classes", [])

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self,
            text="Class Timetable",
            font=ctk.CTkFont(family="Inter", size=22, weight="bold"),
            text_color=Theme.TEXT_MAIN,
        )
        self.title_label.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Top Control Panel
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.add_btn = ctk.CTkButton(
            self.control_frame,
            text="+ Add Class",
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            font=ctk.CTkFont(weight="bold"),
            command=self._add_class_dialog,
        )
        self.add_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            self.control_frame,
            text="Save Timetable",
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            text_color=Theme.BG_DARK,
            font=ctk.CTkFont(weight="bold"),
            command=self._save_timetable,
        )
        self.save_btn.pack(side="left", padx=5)

        # Header Columns
        self.list_header = ctk.CTkFrame(
            self,
            fg_color=Theme.SIDEBAR_BG,
            height=36,
            corner_radius=6,
            border_color=Theme.BORDER,
            border_width=1,
        )
        self.list_header.grid(row=2, column=0, padx=15, pady=(10, 0), sticky="ew")
        self.list_header.grid_propagate(False)
        
        self.list_header.grid_columnconfigure(0, weight=2)
        self.list_header.grid_columnconfigure(1, weight=2)
        self.list_header.grid_columnconfigure(2, weight=2)
        self.list_header.grid_columnconfigure(3, weight=2)
        self.list_header.grid_columnconfigure(4, weight=5)
        self.list_header.grid_columnconfigure(5, weight=2)
        self.list_header.grid_columnconfigure(6, weight=3)

        headers = ["Subject", "Day", "Start", "End", "Google Meet Link", "Enabled", "Actions"]
        for col_idx, text in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.list_header,
                text=text.upper(),
                font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                text_color=Theme.TEXT_MUTED,
                anchor="w",
            )
            lbl.grid(row=0, column=col_idx, padx=15, pady=5, sticky="ew")

        # Scroll Rows Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=3, column=0, padx=15, pady=(5, 15), sticky="nsew")

        self._render_rows()

    def _render_rows(self) -> None:
        """Render the class item list rows."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.classes:
            self.empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="No classes scheduled. Click '+ Add Class' to configure your timetable.",
                font=ctk.CTkFont(slant="italic"),
                text_color=Theme.TEXT_MUTED,
            )
            self.empty_lbl.pack(padx=20, pady=50)
            return

        for idx, class_info in enumerate(self.classes):
            row_card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=Theme.CARD_BG if idx % 2 == 0 else Theme.SIDEBAR_BG,
                border_color=Theme.BORDER,
                border_width=1,
                corner_radius=6,
                height=48,
            )
            row_card.pack(fill="x", pady=3, ipady=3)
            
            row_card.grid_columnconfigure(0, weight=2)
            row_card.grid_columnconfigure(1, weight=2)
            row_card.grid_columnconfigure(2, weight=2)
            row_card.grid_columnconfigure(3, weight=2)
            row_card.grid_columnconfigure(4, weight=5)
            row_card.grid_columnconfigure(5, weight=2)
            row_card.grid_columnconfigure(6, weight=3)

            # Columns
            def add_lbl(text: str, col: int):
                ctk.CTkLabel(
                    row_card,
                    text=text,
                    font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                    text_color=Theme.TEXT_MAIN,
                    anchor="w",
                ).grid(row=0, column=col, padx=15, pady=5, sticky="ew")

            add_lbl(class_info["subject"], 0)
            add_lbl(class_info["day"], 1)
            add_lbl(class_info["start"], 2)
            add_lbl(class_info["end"], 3)

            # Link Input
            link_entry = ctk.CTkEntry(
                row_card,
                height=26,
                fg_color=Theme.BG_DARK,
                border_color=Theme.BORDER,
                text_color=Theme.TEXT_MAIN,
                corner_radius=4,
            )
            link_entry.insert(0, class_info["link"])
            link_entry.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
            link_entry.bind(
                "<FocusOut>",
                lambda event, entry=link_entry, i=idx: self._update_link_in_place(i, entry.get()),
            )

            # Checkbox
            status_var = ctk.BooleanVar(value=class_info.get("enabled", True))
            status_chk = ctk.CTkCheckBox(
                row_card,
                text="",
                variable=status_var,
                width=18,
                checkbox_width=18,
                checkbox_height=18,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                command=lambda var=status_var, i=idx: self._toggle_class(i, var.get()),
            )
            status_chk.grid(row=0, column=5, padx=30, pady=5, sticky="w")

            # Actions
            act_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            act_frame.grid(row=0, column=6, padx=5, pady=5, sticky="ew")

            edit_btn = ctk.CTkButton(
                act_frame,
                text="Edit",
                width=45,
                height=24,
                corner_radius=4,
                fg_color=Theme.WARNING,
                hover_color=Theme.WARNING_HOVER,
                text_color=Theme.BG_DARK,
                font=ctk.CTkFont(weight="bold"),
                command=lambda i=idx: self._edit_class_dialog(i),
            )
            edit_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                act_frame,
                text="Del",
                width=45,
                height=24,
                corner_radius=4,
                fg_color=Theme.DANGER,
                hover_color=Theme.DANGER_HOVER,
                text_color=Theme.TEXT_MAIN,
                font=ctk.CTkFont(weight="bold"),
                command=lambda i=idx: self._delete_class(i),
            )
            del_btn.pack(side="left", padx=2)

    def _update_link_in_place(self, index: int, new_link: str) -> None:
        if index < len(self.classes):
            self.classes[index]["link"] = new_link.strip()

    def _toggle_class(self, index: int, status: bool) -> None:
        if index < len(self.classes):
            self.classes[index]["enabled"] = status
            self._save_timetable()

    def _add_class_dialog(self) -> None:
        ClassDialog(self, title="Add Class", on_save=self._add_class)

    def _add_class(self, new_class: dict[str, Any]) -> None:
        self.classes.append(new_class)
        self._render_rows()

    def _edit_class_dialog(self, index: int) -> None:
        if index < len(self.classes):
            ClassDialog(
                self,
                title="Edit Class",
                on_save=lambda data: self._edit_class(index, data),
                initial_data=self.classes[index],
            )

    def _edit_class(self, index: int, updated_class: dict[str, Any]) -> None:
        if index < len(self.classes):
            self.classes[index] = updated_class
            self._render_rows()

    def _delete_class(self, index: int) -> None:
        if index < len(self.classes):
            self.classes.pop(index)
            self._render_rows()

    def _save_timetable(self) -> None:
        config = self.config_manager.get_config()
        config["classes"] = self.classes
        self.config_manager.save_config(config)
        
        old_text = self.title_label.cget("text")
        self.title_label.configure(text="Timetable Saved Successfully!", text_color=Theme.SUCCESS)
        self.after(2000, lambda: self.title_label.configure(text=old_text, text_color=Theme.TEXT_MAIN))
