# -*- coding: utf-8 -*-


import shutil
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List, NamedTuple

from clifs import ClifsPlugin
from clifs.utils_cli import AnsiColor, cli_bar, size2str, wrap_string


class UsageInfo(NamedTuple):
    """Disk usage info"""

    total: int
    used: int
    free: int


class DiscUsageExplorer(ClifsPlugin):
    """
    Display disk usage for one or more directories.
    """

    dirs: List[str]

    @staticmethod
    def init_parser(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        parser.add_argument(
            "dirs",
            type=str,
            default=".",
            nargs="*",
            help="Directory or directories do get info from.",
        )

    def __init__(self, args) -> None:
        super().__init__(args)
        self._dict_usage: Dict[str, UsageInfo] = self._get_usage_info()

    def run(self) -> None:
        self._print_usage_info()

    def _get_usage_info(self) -> Dict[str, UsageInfo]:
        disc_usage = {}
        for directory in self.dirs:
            disc_usage[directory] = UsageInfo(*shutil.disk_usage(directory))
        return disc_usage

    def _print_usage_info(self) -> None:
        print("")
        for directory, usage_info in self._dict_usage.items():
            name_dir = Path(directory).name if Path(directory).name != "" else directory
            path_dir = str(Path(directory).resolve())
            print(
                name_dir + "    " + wrap_string(f"({path_dir})", prefix=AnsiColor.GRAY)
            )
            if frac_used := (usage_info.used / usage_info.total) <= 0.7:
                color = AnsiColor.DEFAULT
            elif frac_used <= 0.9:
                color = AnsiColor.YELLOW
            else:
                color = AnsiColor.RED

            str_total = size2str(usage_info.total, ansi_color=AnsiColor.DEFAULT)
            str_used = size2str(usage_info.used, ansi_color=AnsiColor.DEFAULT)
            str_free = size2str(usage_info.free, ansi_color=color)

            usage_bar = wrap_string(
                cli_bar(usage_info.used, usage_info.total, print_out=False),
                prefix=color,
            )

            print(
                f"  └── {usage_bar}    "
                f"total: {str_total}    "
                f"used: {str_used}    "
                f"free: {str_free}"
            )
