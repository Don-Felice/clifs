# -*- coding: utf-8 -*-


from argparse import ArgumentParser
from pathlib import Path
import shutil
from typing import List, Dict

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_cli import wrap_string, ANSI_COLORS, size2str, cli_bar


class DiscUsageExplorer(ClifsPlugin):
    """
    Display a tree of the file system including item sizes.
    """

    dirs: List[str]
    _dict_usage: dict

    @staticmethod
    def init_parser(parser: ArgumentParser):
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

    def __init__(self, args):
        super().__init__(args)
        self._dict_usage = self._get_usage_info()

    def run(self):
        self._print_usage_info()
        pass

    def _get_usage_info(self) -> Dict[str, Dict[str, int]]:
        disc_usage = {}
        for directory in self.dirs:
            dict_usage = {}
            (
                dict_usage["total"],
                dict_usage["used"],
                dict_usage["free"],
            ) = shutil.disk_usage(directory)
            disc_usage[directory] = dict_usage
        return disc_usage

    def _print_usage_info(self):
        print("")
        for directory, dict_usage in self._dict_usage.items():
            name_dir = (
                Path(directory).name if not Path(directory).name == "" else directory
            )
            path_dir = str(Path(directory).resolve())
            print(
                name_dir
                + "    "
                + wrap_string("(" + path_dir + ")", prefix=ANSI_COLORS["gray"])
            )
            if dict_usage["used"] / dict_usage["total"] > 0.9:
                color = ANSI_COLORS["red"]
            elif dict_usage["used"] / dict_usage["total"] > 0.70:
                color = ANSI_COLORS["yellow"]
            else:
                color = ANSI_COLORS["default"]

            str_total = size2str(
                dict_usage["total"], ansiescape_color=ANSI_COLORS["default"]
            )
            str_used = size2str(
                dict_usage["used"], ansiescape_color=ANSI_COLORS["default"]
            )
            str_free = size2str(dict_usage["free"], ansiescape_color=color)

            usage_bar = wrap_string(
                cli_bar(dict_usage["used"], dict_usage["total"], return_string=True),
                prefix=color,
            )

            print(
                f"  ????????? {usage_bar}    "
                f"total: {str_total}    "
                f"used: {str_used}    "
                f"free: {str_free}"
            )
