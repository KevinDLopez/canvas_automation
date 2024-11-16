import datetime
from typing import Literal
from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


CURRENT_LOG_LEVEL = LogLevel.DEBUG


def set_log_level(level: LogLevel):
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = level


def Print(*args, type: Literal["DEBUG", "INFO", "ERROR", "WARN"] = "DEBUG"):
    log_levels = {"DEBUG": LogLevel.DEBUG, "INFO": LogLevel.INFO, "WARN": LogLevel.WARN, "ERROR": LogLevel.ERROR}

    # Check if the message should be printed based on current log level
    if log_levels[type] < CURRENT_LOG_LEVEL:
        return

    colors = {"INFO": "\033[90m", "ERROR": "\033[91m", "DEBUG": "\033[37m", "WARN": "\033[93m"}
    reset = "\033[0m"
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    left_padding = " " * ((9 - len(type)) // 2)
    right_padding = " " * ((8 - len(type)) // 2)
    formatted_message = (
        f"{colors[type]}[{left_padding}{type}{right_padding}] - {timestamp} - {' '.join(map(str, args))}{reset}"
    )
    print(formatted_message)


Print("This is a debug message", type="DEBUG")
Print("asd", "asdf", type="INFO")
arr = [1, 2, 3]
Print("This is a warning message", arr, type="WARN")
obj = {"key": "value"}
Print("This is an error message", obj, type="ERROR")
