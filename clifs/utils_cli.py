"""
Utilities for the command line interface
"""

from enum import Enum
from typing import Union


class AnsiColor(str, Enum):
    """Ansi escape colors."""

    DEFAULT = "\033[0m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    GRAY = "\033[0;90m"
    GREEN = "\033[0;32m"
    MAGENTA = "\033[0;35m"
    RED = "\033[0;31m"
    WHITE = "\033[0;37m"
    YELLOW = "\033[0;93m"

    def __str__(self) -> str:
        return self.value


def wrap_string(
    string: str,
    prefix: Union[str, AnsiColor] = AnsiColor.RED,
    suffix: Union[str, AnsiColor] = AnsiColor.DEFAULT,
) -> str:
    return f"{prefix}{string}{suffix}"


def size2str(size: float, ansi_color: AnsiColor = AnsiColor.CYAN) -> str:
    if size < 1024**2:
        unit = "KB"
        size = round(size / 1024, 2)
    elif size < 1024**3:
        unit = "MB"
        size = round(size / 1024**2, 2)
    elif size < 1024**4:
        unit = "GB"
        size = round(size / 1024**3, 2)
    elif size < 1024**5:
        unit = "TB"
        size = round(size / 1024**4, 2)
    else:
        unit = "PB"
        size = round(size / 1024**5, 2)
    return wrap_string(f"{size:7.2f} {unit}", prefix=ansi_color)


def cli_bar(
    status: int,
    total: int,
    suffix: str = "",
    print_out: bool = True,
    bar_len: int = 20,
) -> str:
    filled_len = int(round(bar_len * status / float(total)))
    percents = round(100.0 * status / float(total), 1)
    res_bar = "█" * filled_len + "-" * (bar_len - filled_len)
    output = f"|{res_bar}| {percents:5}% {suffix}"
    if print_out:
        print(output, flush=True)
    return output


def user_query(message: str) -> bool:
    yes = {"yes", "y"}
    print(message)
    choice = input().lower()
    return choice in yes


def print_line(length: int = 50) -> None:
    print("—" * length)
