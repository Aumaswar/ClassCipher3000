"""Browser session and Google Meet lifecycle manager with GUI state integration."""

from __future__ import annotations

import re
import time
from typing import Any

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from core.bot_state import state
from core.join_meet import attempt_join, disable_camera, disable_microphone
from core.logger import BotLogger


class MeetingManager:
    """Manages the lifecycle of the browser and Google Meet interactions, syncing with UI."""

    JOIN_PAGE_TIMEOUT_MS = 60_000
    PRE_JOIN_WAIT_MS = 3_000

    def __init__(self, config: dict[str, Any], logger: BotLogger, profile_dir: str) -> None:
        self._config = config
        self._logger = logger
        self._profile_dir = profile_dir
        self._meeting = config["meeting"]
        self._browser = config["browser"]

        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page | None:
        """Return the active page instance."""
        return self._page

    def is_browser_open(self) -> bool:
        """Return True if Playwright, browser context, and page are active and responsive."""
        if self._playwright is None or self._context is None or self._page is None:
            return False
        try:
            if self._page.is_closed():
                return False
            self._page.evaluate("1 + 1")
            return True
        except Exception:
            return False

    def open_meet(self, meet_link: str) -> Page:
        """Launch Google Chrome with the persistent profile and navigate to the Meet link."""
        state.status_text = "Starting browser..."
        self._logger.info("Starting Playwright browser engine...")
        self._playwright = sync_playwright().start()

        permissions = []
        if self._browser.get("accept_permissions", True):
            permissions = ["microphone", "camera"]

        launch_args = []
        if self._browser.get("maximize_window", True):
            launch_args.append("--start-maximized")

        self._logger.info(f"Launching Chrome with profile from: {self._profile_dir}")
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=self._profile_dir,
            channel="chrome",
            headless=self._browser.get("headless", False),
            slow_mo=self._browser.get("slow_mo", 0),
            permissions=permissions,
            args=launch_args,
            no_viewport=True if self._browser.get("maximize_window", True) else None,
        )

        self._page = self._context.new_page()
        # Save page reference to global shared GUI state
        state.active_page = self._page

        self._logger.info(f"Navigating to: {meet_link}")
        state.status_text = "Navigating to Meet..."
        
        self._page.goto(
            meet_link,
            wait_until="networkidle",
            timeout=self.JOIN_PAGE_TIMEOUT_MS,
        )
        return self._page

    def prepare_and_join(self, page: Page) -> str:
        """Turn off mic/camera and attempt to join Google Meet with retries."""
        try:
            if not state.bot_active:
                return "failed"

            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(self.PRE_JOIN_WAIT_MS)

            # Check if already inside meeting room
            if self.is_in_meeting(page):
                self._logger.info("Already inside the meeting call.")
                return "joined"

            # Mute Microphone
            if self._meeting.get("mute_microphone", True):
                state.status_text = "Muting microphone..."
                disable_microphone(page, self._logger)
                
            # Disable Camera
            if self._meeting.get("disable_camera", True):
                state.status_text = "Disabling camera..."
                disable_camera(page, self._logger)

            page.wait_for_timeout(1_000)

            retries = self._meeting.get("max_join_retries", 3)
            interval = self._meeting.get("retry_interval_seconds", 20)

            for attempt in range(1, retries + 1):
                if not state.bot_active:
                    return "failed"
                if page.is_closed():
                    self._logger.warning("Meeting tab was closed during join attempts.")
                    return "failed"

                # Check if transitioned/admitted during retries
                if self.is_in_meeting(page):
                    self._logger.info("Transitioned into meeting call.")
                    return "joined"

                state.status_text = f"Joining (attempt {attempt}/{retries})..."
                status = attempt_join(page, self._logger)
                if status != "failed":
                    return status

                if attempt < retries and self._meeting.get("retry_join", True):
                    self._logger.warning(
                        f"Join attempt {attempt}/{retries} failed. Retrying in {interval}s..."
                    )
                    # Sleep responsively
                    for _ in range(interval):
                        if not state.bot_active:
                            return "failed"
                        page.wait_for_timeout(1000)

            return "failed"
        except Exception as exc:
            self._logger.error(f"Error during prepare and join: {exc}")
            return "failed"

    def is_in_meeting(self, page: Page) -> bool:
        """Return True if we are inside the call (the leave button is visible)."""
        try:
            if page.is_closed():
                return False
            leave_patterns = [
                re.compile(r"leave call", re.I),
                re.compile(r"leave meeting", re.I),
                re.compile(r"\bleave\b", re.I),
            ]
            for pattern in leave_patterns:
                locator = page.get_by_role("button", name=pattern)
                if locator.count() > 0 and locator.first.is_visible():
                    return True
        except Exception:
            pass
        return False

    def is_waiting_room(self, page: Page) -> bool:
        """Return True if we are waiting for host admission."""
        try:
            if page.is_closed():
                return False
            waiting_texts = [
                "asking to be let in",
                "lets you in",
                "waiting for host",
                "waiting for the host",
            ]
            for text in waiting_texts:
                locator = page.get_by_text(text, exact=False)
                if locator.count() > 0 and any(locator.nth(i).is_visible() for i in range(locator.count())):
                    return True
        except Exception:
            pass
        return False

    def wait_for_in_meeting(self, page: Page, timeout_seconds: int = 15) -> bool:
        """Wait until we are fully inside the meeting call (the leave button is visible)."""
        start_time = time.time()
        self._logger.info("Waiting for meeting transition to complete...")
        state.status_text = "Connecting to call..."
        
        while time.time() - start_time < timeout_seconds:
            if not state.bot_active:
                return False
            if page.is_closed():
                return False
            if self.is_in_meeting(page):
                self._logger.info("Successfully inside the meeting room.")
                state.status_text = "In Meeting"
                return True
            time.sleep(0.5)
            
        self._logger.warning("Timed out waiting for transition to meeting call.")
        return False

    def wait_for_admission(self, page: Page) -> bool:
        """Wait for the host to admit us to the meeting or time out."""
        if not self._meeting.get("wait_for_host", True):
            return True

        max_wait_seconds = self._meeting.get("max_wait_minutes", 30) * 60
        poll_interval = self._meeting.get("retry_interval_seconds", 20)
        elapsed = 0

        self._logger.info("Waiting for host admission...")
        state.status_text = "Waiting for host admission..."
        while elapsed < max_wait_seconds:
            if not state.bot_active:
                return False
            if page.is_closed():
                self._logger.warning("Browser tab closed while waiting for host admission.")
                return False

            if self.is_in_meeting(page):
                self._logger.info("Host approved entry. We are in the meeting!")
                state.status_text = "In Meeting"
                return True

            if not self.is_waiting_room(page):
                self._logger.warning("No longer in waiting room and not in meeting. State lost.")
                return False

            # Sleep responsively
            for _ in range(poll_interval):
                if not state.bot_active:
                    return False
                page.wait_for_timeout(1000)
            elapsed += poll_interval

        self._logger.warning("Timed out waiting for host admission.")
        return False

    def leave_meeting(self, page: Page) -> bool:
        """Click the leave/hangup button to exit the call."""
        self._logger.info("Attempting to leave meeting...")
        state.status_text = "Leaving meeting..."
        try:
            if page.is_closed():
                return True
            leave_patterns = [
                re.compile(r"leave call", re.I),
                re.compile(r"leave meeting", re.I),
                re.compile(r"\bleave\b", re.I),
            ]
            for pattern in leave_patterns:
                button = page.get_by_role("button", name=pattern)
                if button.count() > 0 and button.first.is_visible():
                    button.first.click()
                    self._logger.info("Clicked leave meeting button.")
                    return True
        except Exception as exc:
            self._logger.warning(f"Error while attempting to leave meeting: {exc}")
        return False

    def close(self) -> None:
        """Close browser page, browser context, and stop Playwright cleanly."""
        self._logger.info("Shutting down browser and Playwright...")
        
        if self._page is not None:
            try:
                self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        
        # Clear global GUI page reference
        state.active_page = None
        self._logger.info("Browser closed.")
