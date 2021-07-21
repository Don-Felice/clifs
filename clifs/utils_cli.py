# -*- coding: utf-8 -*-


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


def wrap_string(string, prefix=ANSI_COLORS["red"], suffix=ANSI_COLORS["default"]):
    return prefix + string + suffix


def size2str(size, ansiescape_color=ANSI_COLORS["cyan"]):
    if size >= (1024 ** 5):
        unit = "PB"
        size = round(size / (1024 ** 5), 2)
    elif size >= (1024 ** 4):
        unit = "TB"
        size = round(size / (1024 ** 4), 2)
    elif size >= (1024 ** 3):
        unit = "GB"
        size = round(size / (1024 ** 3), 2)
    else:
        unit = "MB"
        size = round(size / (1024 ** 2), 2)
    return wrap_string(f"{size:6.2f} " + unit, prefix=ansiescape_color)


def cli_bar(status, total, suffix="", return_string=False, bar_len=20):

    filled_len = int(round(bar_len * status / float(total)))
    percents = round(100.0 * status / float(total), 1)
    bar = "█" * filled_len + "-" * (bar_len - filled_len)
    output = f"|{bar}| {percents:5}% {suffix}"
    if return_string:
        return output
    else:
        print(output, flush=True)


def user_query(message):
    yes = {"yes", "y"}
    print(message)
    choice = input().lower()
    if choice in yes:
        return True
    else:
        return False
