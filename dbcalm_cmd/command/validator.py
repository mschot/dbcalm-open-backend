
VALID_REQUEST = 200
INVALID_REQUEST = 400

class Validator:
    def __init__(self) -> None:
        self.commands = {
            "update_cron_schedules": {
                "schedules": "required",
            },
        }

        self.valid_frequencies = ["daily", "weekly", "monthly"]
        self.valid_backup_types = ["full", "incremental"]

    def required_args(self, command: str) -> list:
        return [
                key for key,
                value in self.commands[command].items() if "required" in value
            ]

    def validate_schedule(self, schedule: dict) -> tuple[int, str]:
        """Validate a single schedule object."""
        # Check required fields
        required_fields = ["id", "title", "backup_type", "frequency", "hour", "minute", "enabled"]
        for field in required_fields:
            if field not in schedule:
                return INVALID_REQUEST, f"Schedule missing required field: {field}"

        # Validate backup_type
        if schedule["backup_type"] not in self.valid_backup_types:
            return INVALID_REQUEST, f"Invalid backup_type: {schedule['backup_type']}"

        # Validate frequency
        if schedule["frequency"] not in self.valid_frequencies:
            return INVALID_REQUEST, f"Invalid frequency: {schedule['frequency']}"

        # Validate hour (0-23)
        try:
            hour = int(schedule["hour"])
            if not 0 <= hour <= 23:
                return INVALID_REQUEST, f"Invalid hour: {hour}. Must be 0-23"
        except (ValueError, TypeError):
            return INVALID_REQUEST, f"Invalid hour: {schedule['hour']}"

        # Validate minute (0-59)
        try:
            minute = int(schedule["minute"])
            if not 0 <= minute <= 59:
                return INVALID_REQUEST, f"Invalid minute: {minute}. Must be 0-59"
        except (ValueError, TypeError):
            return INVALID_REQUEST, f"Invalid minute: {schedule['minute']}"

        # Validate day_of_week for weekly schedules
        if schedule["frequency"] == "weekly":
            if "day_of_week" in schedule and schedule["day_of_week"] is not None:
                try:
                    day = int(schedule["day_of_week"])
                    if not 0 <= day <= 6:
                        return INVALID_REQUEST, f"Invalid day_of_week: {day}. Must be 0-6"
                except (ValueError, TypeError):
                    return INVALID_REQUEST, f"Invalid day_of_week: {schedule['day_of_week']}"

        # Validate day_of_month for monthly schedules
        if schedule["frequency"] == "monthly":
            if "day_of_month" in schedule and schedule["day_of_month"] is not None:
                try:
                    day = int(schedule["day_of_month"])
                    if not 1 <= day <= 31:
                        return INVALID_REQUEST, f"Invalid day_of_month: {day}. Must be 1-31"
                except (ValueError, TypeError):
                    return INVALID_REQUEST, f"Invalid day_of_month: {schedule['day_of_month']}"

        return VALID_REQUEST, ""

    def validate(self, command_data: dict) -> tuple[int, str]:
        if command_data["cmd"] not in self.commands:
            return INVALID_REQUEST, "Invalid command"

        # check if all required arguments are present
        for arg in self.required_args(command_data["cmd"]):
            if arg not in command_data["args"]:
                return INVALID_REQUEST, f"Missing required argument {arg}"

        # Validate schedules argument
        if command_data["cmd"] == "update_cron_schedules":
            schedules = command_data["args"].get("schedules")

            if not isinstance(schedules, list):
                return INVALID_REQUEST, "schedules must be a list"

            # Validate each schedule
            for idx, schedule in enumerate(schedules):
                if not isinstance(schedule, dict):
                    return INVALID_REQUEST, f"Schedule at index {idx} must be a dict"

                status, message = self.validate_schedule(schedule)
                if status != VALID_REQUEST:
                    return status, f"Schedule at index {idx}: {message}"

        return VALID_REQUEST, ""
