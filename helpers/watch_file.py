import time
import os


def block_until_file_changes(filepath: str, poll_interval=60, limit=3600):
    limit_time = time.time() + limit
    last_modified = os.path.getmtime(filepath) if os.path.exists(filepath) else 0

    while time.time() <= limit_time:
        if os.path.exists(filepath) and os.path.getmtime(filepath) > last_modified:
            return True

        time.sleep(poll_interval)

    return False
