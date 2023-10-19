# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from clifs import ClifsPlugin
from clifs.utils_cli import user_query
from clifs.utils_fs import FileGetterMixin, rename_files


class FileRenamer(ClifsPlugin, FileGetterMixin):
    """
    Regex-based file renaming.
    """

    re_pattern: str
    substitute: str
    skip_preview: bool

    @classmethod
    def init_parser(cls, parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)

        parser.add_argument(
            "-re",
            "--re_pattern",
            default=".*",
            help="Pattern identifying the substring to be replaced. "
            "Supports syntax from regex module "
            "(https://docs.python.org/3/library/re.html).",
        )
        parser.add_argument(
            "-s",
            "--substitute",
            default="",
            help="String to use as replacement. "
            "You can use \\1 \\2 etc. to refer to matching groups. "
            "A pattern like '(.+)\\.(.+)' in combination "
            "with a replacement like '\\1_suffix.\\2' will append suffixes. "
            "Defaults to empty string.",
        )
        parser.add_argument(
            "-sp",
            "--skip_preview",
            action="store_true",
            help="Skip preview on what would happen and rename right away. "
            "Only for the brave...",
        )

    def __init__(self, args) -> None:
        super().__init__(args)
        self.files2process: List[Path] = self.get_files2process()

    def run(self) -> None:
        self.exit_if_nothing_to_process(self.files2process)

        if not self.skip_preview:
            rename_files(
                self.files2process,
                self.re_pattern,
                self.substitute,
                preview_mode=True,
            )
            if not user_query(
                'If you want to apply renaming, give me a "yes" or "y" now!'
            ):
                print("Will not rename for now. See you soon.")
                sys.exit(0)

        rename_files(
            self.files2process,
            self.re_pattern,
            self.substitute,
            preview_mode=False,
        )
