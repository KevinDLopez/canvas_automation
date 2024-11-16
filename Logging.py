import datetime
from typing import Literal
from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


CURRENT_LOG_LEVEL = LogLevel.INFO


def set_log_level(level: LogLevel):
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = level


def Print(*args, log_type: Literal["DEBUG", "INFO", "ERROR", "WARN"] = "DEBUG"):
    log_levels = {"DEBUG": LogLevel.DEBUG, "INFO": LogLevel.INFO, "WARN": LogLevel.WARN, "ERROR": LogLevel.ERROR}

    # Check if the message should be printed based on current log level
    if log_levels[log_type] < CURRENT_LOG_LEVEL:
        return

    colors = {"INFO": "\033[90m", "ERROR": "\033[91m", "DEBUG": "\033[37m", "WARN": "\033[93m"}
    reset = "\033[0m"
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    left_padding = " " * ((9 - len(log_type)) // 2)
    right_padding = " " * ((8 - len(log_type)) // 2)
    formatted_message = (
        f"{colors[log_type]}[{left_padding}{log_type}{right_padding}] - {timestamp} - {' '.join(map(str, args))}{reset}"
    )
    print(formatted_message)


if __name__ == "__main__":
    Print("This is a debug message", log_type="DEBUG")
    Print("asd", "asdf", log_type="INFO")
    arr = [1, 2, 3]
    Print("This is a warning message", arr, log_type="WARN")
    obj = {"key": "value"}
    Print("This is an error message", obj, log_type="ERROR")
