import time
from datetime import timedelta


class UptimeHelper:
    def __init__(self):
        self.start_time = time.time()

    def get_uptime(self) -> str:
        """Returns the uptime as a human-readable string."""
        uptime_seconds = int(time.time() - self.start_time)
        return str(timedelta(seconds=uptime_seconds))


uptime_helper = UptimeHelper()
