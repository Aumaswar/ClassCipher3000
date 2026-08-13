"""Google Meet join helpers with resilient regex-based button detection."""

from __future__ import annotations

import re
from playwright.sync_api import Page
from core.logger import BotLogger

# RegEx patterns for Meet buttons to ensure high resilience to UI label changes
MIC_OFF_PATTERNS = [
    re.compile(r"turn off microphone", re.I),
    re.compile(r"mute microphone", re.I),
]
CAM_OFF_PATTERNS = [
    re.compile(r"turn off camera", re.I),
    re.compile(r"disable camera", re.I),
]
JOIN_PATTERNS = [
    re.compile(r"\bjoin now\b", re.I),
    re.compile(r"\bjoin meeting\b", re.I),
    re.compile(r"\bjoin\b", re.I),
]
ASK_PATTERNS = [
    re.compile(r"\bask to join\b", re.I),
    re.compile(r"\bask\b", re.I),
]


def click_if_exists(page: Page, name_pattern: re.Pattern) -> bool:
    """Click the first visible button matching the given accessible name pattern."""
    try:
        locator = page.get_by_role("button", name=name_pattern)
        if locator.count() > 0 and locator.first.is_visible():
            locator.first.click()
            return True
    except Exception:
        pass
    return False


def disable_microphone(page: Page, logger: BotLogger) -> None:
    """Turn off the microphone if it is currently on."""
    # Attempt to click "turn off microphone"
    for pattern in MIC_OFF_PATTERNS:
        if click_if_exists(page, pattern):
            logger.info("Microphone turned off successfully.")
            return

    # Check if microphone is already off
    try:
        on_pattern = re.compile(r"turn on microphone", re.I)
        locator = page.get_by_role("button", name=on_pattern)
        if locator.count() > 0 and locator.first.is_visible():
            logger.info("Microphone is already off.")
            return
    except Exception:
        pass

    logger.warning("Could not definitively determine or modify microphone state.")


def disable_camera(page: Page, logger: BotLogger) -> None:
    """Turn off the camera if it is currently on."""
    # Attempt to click "turn off camera"
    for pattern in CAM_OFF_PATTERNS:
        if click_if_exists(page, pattern):
            logger.info("Camera turned off successfully.")
            return

    # Check if camera is already off
    try:
        on_pattern = re.compile(r"turn on camera", re.I)
        locator = page.get_by_role("button", name=on_pattern)
        if locator.count() > 0 and locator.first.is_visible():
            logger.info("Camera is already off.")
            return
    except Exception:
        pass

    logger.warning("Could not definitively determine or modify camera state.")


def attempt_join(page: Page, logger: BotLogger) -> str:
    """Try to click 'Join now' or 'Ask to join'.

    Returns one of: "joined", "waiting", or "failed".
    """
    logger.info("Locating meeting entry buttons...")

    # 1. Try to join immediately (direct access)
    for pattern in JOIN_PATTERNS:
        if click_if_exists(page, pattern):
            logger.info("Clicked 'Join Now' button.")
            return "joined"

    # 2. Try to ask for admission (guest access)
    for pattern in ASK_PATTERNS:
        if click_if_exists(page, pattern):
            logger.info("Clicked 'Ask to Join' button.")
            return "waiting"

    logger.warning("Failed to locate any join or ask button.")
    return "failed"
