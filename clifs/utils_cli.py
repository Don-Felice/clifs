"""
Utilities for the command line interface
"""

from typing import Union

ANSI_COLORS = {
    "yellow": "\033[0;93m",
    "cyan": "\033[0;36m",
    "red": "\033[0;31m",
    "green": "\033[0;32m",
    "blue": "\033[0;34m",
    "magenta": "\033[0;35m",
    "white": "\033[0;37m",
    "gray": "\033[0;90m",
    "default": "\033[0m",
}


def wrap_string(
    string: str, prefix: str = ANSI_COLORS["red"], suffix: str = ANSI_COLORS["default"]
) -> str:
    return prefix + string + suffix


def size2str(
    size: Union[int, float], ansiescape_color: str = ANSI_COLORS["cyan"]
) -> str:
    if size >= (1024**5):
        unit = "PB"
        size = round(size / (1024**5), 2)
    elif size >= (1024**4):
        unit = "TB"
        size = round(size / (1024**4), 2)
    elif size >= (1024**3):
        unit = "GB"
        size = round(size / (1024**3), 2)
    else:
        unit = "MB"
        size = round(size / (1024**2), 2)
    return wrap_string(f"{size:6.2f} " + unit, prefix=ansiescape_color)


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
    return bool(choice in yes)


def print_line(length: int = 50) -> None:
    print("—" * length)
