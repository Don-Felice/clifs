# -*- coding: utf-8 -*-

ansiescape_colors = {
    'yellow': '\033[0;93m',
    'cyan': '\033[0;36m',
    'red': '\033[0;31m',
    'green': '\033[0;32m',
    'blue': '\033[0;34m',
    'magenta': '\033[0;35m',
    'white': '\033[0;37m',
    'default': '\033[0m'
}


def wrap_string(string, prefix= ansiescape_colors['red'], suffix=ansiescape_colors['default']):
    return prefix + string + suffix
