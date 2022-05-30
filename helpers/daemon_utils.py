import os
from typing import Callable, List, Optional
import time


def operation_file(file_path, mode, message=""):
    if os.path.exists(file_path):
        if mode == "r":
            with open(f"{file_path}", mode) as f:
                return f.read()
        elif mode == "w" or mode == "a":
            with open(f"{file_path}", mode) as f:
                return f.write(message+"\n")
    else:
        if mode == "w" or mode == "a":
            with open(f"{file_path}", mode) as f:
                return f.write(message+"\n")
        else:
            return ""

def get_currentTime(add_seconds=0):
    return int((time.time() + add_seconds ) * (10 ** 6))

def validate_timeout(start_time, TIMEOUT):
    now = get_currentTime()
    end_time = start_time + (TIMEOUT * (10 ** 6)) 

    # print(f"Falta: {end_time - now}")

    if now <= end_time:
        return True
    else:
        return False

def create_pid_file(fpath: str) -> bool:
    pid = os.getpid()

    if not os.path.exists(fpath):
        with open(fpath, "w") as pid_file:
            pid_file.write(str(pid))
        return True
    else:
        return False


class TempDirQueue:
    def __init__(self, dirpath: str, create=True) -> None:
        self.dirpath = dirpath
        if create and not os.path.exists(dirpath):
            os.makedirs(self.dirpath)

    def consume_entry(self):
        entry = self._get_next_entry()

        if not os.path.exists(entry):
            raise Exception("Entry does not exist.")

        with open(entry, "r") as f:
            contents = f.read()

        os.remove(entry)
        return contents

    def add_entry(self, entry, contents):
        entry = os.path.join(self.dirpath, entry)
        if os.path.exists(entry):
            raise Exception("Entry already exists.")

        with open(entry, "w") as f:
            f.write(contents)

    def is_empty(self) -> bool:
        return not bool(
            next(
                filter(
                    os.path.isfile,
                    map(
                        lambda x: os.path.join(self.dirpath, x),
                        os.listdir(self.dirpath),
                    ),
                ),
                None,
            )
        )

    def _list_entries(self) -> List[str]:
        return list(
            filter(
                os.path.isfile,
                map(
                    lambda x: os.path.join(self.dirpath, x),
                    os.listdir(self.dirpath),
                ),
            ),
        )

    def _get_next_entry(self) -> Optional[str]:
        files = self._list_entries()

        if not len(files) > 0:
            return None

        files.sort()
        return files[0]


class PollingIterator:
    def __init__(self, poll_ready: Callable, get_next: Callable, period: float) -> None:
        self.poll_ready = poll_ready
        self.get_next = get_next
        self.period = period

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if self.poll_ready():
                return self.get_next()
            else:
                time.sleep(self.period)
