"""Clifs plugin to show disc usage"""


import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Dict, List, NamedTuple

from clifs import ClifsPlugin
from clifs.utils_cli import cli_bar, set_style, size2str


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

    def __init__(self, args: Namespace) -> None:
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
        self.console.print()
        for directory, usage_info in self._dict_usage.items():
            name_dir = Path(directory).name if Path(directory).name != "" else directory
            path_dir = str(Path(directory).resolve())
            self.console.print(
                name_dir + "    " + set_style(f"({path_dir})", "bright_black")
            )
            if (frac_used := usage_info.used / usage_info.total) <= 0.7:
                color = "default"
            elif frac_used <= 0.9:
                color = "yellow"
            else:
                color = "red"

            str_total = size2str(usage_info.total, color="default")
            str_used = size2str(usage_info.used, color="default")
            str_free = size2str(usage_info.free, color=color)

            usage_bar = set_style(
                cli_bar(usage_info.used, usage_info.total, print_out=False), color
            )

            self.console.print(
                f"  └── {usage_bar}"
                f"    total: {str_total}"
                f"    used: {str_used}"
                f"    free: {str_free}"
            )
