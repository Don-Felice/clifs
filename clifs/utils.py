# -*- coding: utf-8 -*-

ansiescape_colors = {
    'yellow': '\033[0;93m',
    'cyan': '\033[0;36m',
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'blue': '\033[0;34m',
    'magenta': '\033[0;35m',
    'white': '\033[0;37m',
    'gray': '\033[0;90m',
    'default': '\033[0m',
}


def wrap_string(string, prefix=ansiescape_colors['red'], suffix=ansiescape_colors['default']):
    return prefix + string + suffix


def size2str(size, ansiescape_color=ansiescape_colors['cyan']):
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
