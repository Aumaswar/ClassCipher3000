"""Google Meet Attendance Bot — GUI launcher and background coordinator."""

from __future__ import annotations

import time
import traceback
from datetime import datetime, timedelta

from core.bot_state import state
from core.config_manager import ConfigManager
from core.logger import BotLogger
from core.meeting_manager import MeetingManager
from core.meeting_monitor import MeetingMonitor
from core.scheduler import ClassScheduler
from core.utils import class_label
from ui.dashboard import Dashboard


def run_bot_worker(config_manager: ConfigManager) -> None:
    """Background worker function executing the main bot schedule and meeting join loop."""
    config = config_manager.get_config()
    paths = config_manager.ensure_directories()

    logger = BotLogger(
        log_dir=paths["logs"],
        level=config["logging"].get("level", "INFO"),
        console=config["logging"].get("save_console", True),
    )

    logger.info("Background bot worker thread initialized.")
    scheduler = ClassScheduler(config_manager, logger)

    while state.bot_active:
        try:
            # Reload configurations from disk
            config = config_manager.get_config()
            paths = config_manager.ensure_directories()

            # Wait for next scheduled class (blocks until class opens or stopped)
            current_class = scheduler.wait_for_next_class()
            if current_class is None:
                # Stops thread if scheduler returns None (bot stopped or empty schedule)
                break

            logger.info(f"Starting session: {class_label(current_class)}")
            state.attendance_marked = False
            leave_late_delta = timedelta(minutes=scheduler.leave_late_minutes)
            leave_at_dt = current_class["end_dt"] + leave_late_delta

            completed_successfully = False

            # Session rejoin/retry loop
            while state.bot_active:
                now = datetime.now()
                if now >= leave_at_dt:
                    logger.info("Class session duration expired.")
                    break

                # Cancel and exit if manual stop/leave override requested
                if state.force_action == "leave_meeting":
                    state.force_action = None
                    break

                manager = MeetingManager(
                    config=config,
                    logger=logger,
                    profile_dir=str(paths["profile"]),
                )

                try:
                    page = manager.open_meet(current_class["link"])
                    status = manager.prepare_and_join(page)
                    logger.info(f"Meeting join attempt status: {status}")

                    if status == "failed":
                        logger.warning("Join attempt failed. Re-trying in 20 seconds...")
                        manager.close()
                        # Responsive sleep loop
                        for _ in range(20):
                            if not state.bot_active:
                                break
                            time.sleep(1)
                        continue

                    # Wait for transition/admission based on join status
                    admitted = False
                    if status == "joined":
                        admitted = manager.wait_for_in_meeting(page)
                    elif status == "waiting":
                        admitted = manager.wait_for_admission(page)

                    if not admitted:
                        logger.warning("Failed to enter meeting call (denied or timed out). Re-trying...")
                        manager.close()
                        for _ in range(20):
                            if not state.bot_active:
                                break
                            time.sleep(1)
                        continue

                    # Admitted successfully!
                    logger.info("Successfully entered meeting call. Running monitor...")
                    monitor = MeetingMonitor(
                        config=config,
                        logger=logger,
                        paths=paths,
                    )
                    
                    # Blocks until class end, tab close, or user stop command
                    run_status = monitor.run(page, current_class, leave_at_dt)

                    if run_status == "completed":
                        logger.info("Session finished. Gracefully leaving Meet call...")
                        manager.leave_meeting(page)
                        completed_successfully = True
                        manager.close()
                        break
                    elif run_status == "stopped":
                        logger.info("Meeting exited due to Stop Bot command.")
                        manager.leave_meeting(page)
                        manager.close()
                        break
                    elif run_status == "manual_leave":
                        logger.info("Meeting exited due to manual Leave command. Setting class as completed.")
                        manager.leave_meeting(page)
                        completed_successfully = True
                        manager.close()
                        break
                    else:
                        logger.warning("Left meeting early (disconnected). Retrying rejoin...")
                        manager.close()
                        for _ in range(10):
                            if not state.bot_active:
                                break
                            time.sleep(1)

                except Exception as exc:
                    logger.error(f"Error occurred during meeting session: {exc}")
                    logger.debug(traceback.format_exc())
                    manager.close()
                    for _ in range(10):
                        if not state.bot_active:
                            break
                        time.sleep(1)

            if completed_successfully:
                scheduler.mark_completed(current_class)

            logger.info("Waiting for next scheduled class...")
            for _ in range(int(config["meeting"].get("post_meeting_delay_seconds", 5))):
                if not state.bot_active:
                    break
                time.sleep(1)

        except Exception as exc:
            logger.error(f"Global worker exception: {exc}")
            logger.debug(traceback.format_exc())
            time.sleep(5)

    # Clean shut down state fields
    state.bot_active = False
    state.status_text = "Stopped"
    state.countdown_text = "N/A"
    state.current_class_label = "None"
    state.current_meeting_link = ""
    logger.info("Background bot worker thread terminated cleanly.")


def main() -> None:
    """Launch the Google Meet Attendance Bot CustomTkinter Dashboard UI."""
    config_manager = ConfigManager()
    
    # Instantiate and start the CTk application main loop
    app = Dashboard(config_manager, run_bot_worker)
    app.mainloop()


if __name__ == "__main__":
    main()
