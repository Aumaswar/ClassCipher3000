from datetime import datetime, timedelta
import time

from core.bot_state import state


CHECK_INTERVAL = 30
EARLY_JOIN_MINUTES = 5


def time_to_minutes(time_str):
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def get_today_classes(config):
    today = datetime.now().strftime("%A")

    classes = [
        cls for cls in config.get("classes", [])
        if cls.get("day") == today
    ]

    classes.sort(key=lambda c: time_to_minutes(c["start"]))

    return classes


class ClassScheduler:

    def __init__(self, config_manager, logger):
        self.config_manager = config_manager
        self.logger = logger

        config = config_manager.get_config()

        meeting_config = config.get("meeting", {})

        self.early_join_minutes = meeting_config.get(
            "join_early_minutes",
            EARLY_JOIN_MINUTES
        )

        self.leave_late_minutes = meeting_config.get(
            "leave_late_minutes",
            5
        )

        self.check_interval = CHECK_INTERVAL

    def _class_id(self, cls):
        return (
            cls.get("day"),
            cls.get("subject"),
            cls.get("start")
        )

    def _prepare_class(self, cls):
        today = datetime.now().date()

        start_hour, start_minute = map(
            int,
            cls["start"].split(":")
        )

        end_hour, end_minute = map(
            int,
            cls["end"].split(":")
        )

        start_dt = datetime.combine(
            today,
            datetime.min.time()
        ).replace(
            hour=start_hour,
            minute=start_minute
        )

        end_dt = datetime.combine(
            today,
            datetime.min.time()
        ).replace(
            hour=end_hour,
            minute=end_minute
        )

        # Handles classes that cross midnight.
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        prepared = dict(cls)

        prepared["start_dt"] = start_dt
        prepared["end_dt"] = end_dt

        return prepared

    def wait_for_next_class(self):
        while state.bot_active:

            config = self.config_manager.get_config()

            today_classes = get_today_classes(config)

            if not today_classes:
                self.logger.info("No classes scheduled for today.")
                return None

            now = datetime.now()

            next_future = None

            for raw_class in today_classes:

                cls = self._prepare_class(raw_class)

                class_id = self._class_id(cls)

                if class_id in state.completed_classes:
                    continue

                start_dt = cls["start_dt"]
                end_dt = cls["end_dt"]

                early_join_dt = (
                    start_dt -
                    timedelta(minutes=self.early_join_minutes)
                )

                # Class is currently running.
                if start_dt <= now < end_dt:
                    self.logger.info(
                        f"Class already running: {cls['subject']}"
                    )
                    return cls

                # Class is within early-join window.
                if early_join_dt <= now < start_dt:
                    self.logger.info(
                        f"Early join window reached: "
                        f"{cls['subject']}"
                    )
                    return cls

                # Find the next future class.
                if now < early_join_dt:
                    if next_future is None:
                        next_future = cls

            if next_future is None:
                self.logger.info("No more classes today.")
                return None

            seconds_until_join = (
                next_future["start_dt"]
                - timedelta(minutes=self.early_join_minutes)
                - now
            ).total_seconds()

            if seconds_until_join > 0:
                join_time = next_future["start_dt"] - timedelta(minutes=self.early_join_minutes)
                
                state.current_class_label = f"{next_future['subject']} ({next_future['start']})"
                state.current_meeting_link = next_future["link"]
                state.status_text = "Waiting for schedule..."

                self.logger.info(
                    f"Waiting for {next_future['subject']} ({next_future['start']}) - "
                    f"join window in {int(seconds_until_join // 60)}m {int(seconds_until_join % 60)}s"
                )

                while datetime.now() < join_time:
                    if not state.bot_active:
                        state.status_text = "Stopped"
                        state.countdown_text = "N/A"
                        return None

                    if state.force_action == "join_now":
                        break

                    # Format countdown
                    remaining = max(0, int((join_time - datetime.now()).total_seconds()))
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60
                    seconds = remaining % 60
                    state.countdown_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                    time.sleep(1)

                if state.force_action == "join_now":
                    state.force_action = None
                    self.logger.info("Manual 'Join Now' override triggered. Bypassing wait timer.")
                    state.status_text = "Joining (Manual Override)..."
                    return next_future

            else:
                return next_future

        return None

    def mark_completed(self, cls):
        class_id = self._class_id(cls)

        state.completed_classes.add(class_id)

        self.logger.info(
            f"Marked class as completed: "
            f"{cls.get('subject', 'Unknown')} "
            f"({cls.get('start', 'Unknown')})"
        )