"""Shared helpers and constants for time parsing and class scheduling."""

from __future__ import annotations

import re
from datetime import datetime, date, time, timedelta
from typing import Any

# Polling interval when waiting for the next class (seconds)
SCHEDULER_POLL_SECONDS = 10

# How often the meeting monitor checks leave time and presence (seconds)
MEETING_POLL_SECONDS = 10

# Regular expression to clean and extract meet link
MEET_LINK_PATTERN = re.compile(r"meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}")


def class_label(class_info: dict[str, Any]) -> str:
    """Return a human-readable label for a class session."""
    return f"{class_info['subject']} ({class_info['day']} {class_info['start']}-{class_info['end']})"


def get_next_weekday_date(day_name: str, start_from: date) -> date:
    """Return the date of the next occurrence of a weekday (including today if it matches)."""
    weekdays = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    target_idx = weekdays.index(day_name.strip().lower())
    current_idx = start_from.weekday()

    days_ahead = target_idx - current_idx
    if days_ahead < 0:
        days_ahead += 7

    return start_from + timedelta(days=days_ahead)


def parse_time(time_str: str) -> time:
    """Parse an HH:MM string into a datetime.time object."""
    dt = datetime.strptime(time_str.strip(), "%H:%M")
    return dt.time()


def get_class_datetimes(
    class_info: dict[str, Any], date_val: date
) -> tuple[datetime, datetime]:
    """Return (start_datetime, end_datetime) for a class on a specific date."""
    start_time = parse_time(class_info["start"])
    end_time = parse_time(class_info["end"])
    start_dt = datetime.combine(date_val, start_time)
    end_dt = datetime.combine(date_val, end_time)
    return start_dt, end_dt
