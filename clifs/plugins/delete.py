# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from clifs import ClifsPlugin
from clifs.utils_cli import user_query
from clifs.utils_fs import FileGetterMixin, delete_files


class FileDeleter(ClifsPlugin, FileGetterMixin):
    """
    Delete files
    """

    skip_preview: bool

    @classmethod
    def init_parser(cls, parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)

        parser.add_argument(
            "-sp",
            "--skip_preview",
            action="store_true",
            help="Skip preview on what would happen and delete right away. "
            "For the brave only...",
        )

    def __init__(self, args) -> None:
        super().__init__(args)
        self.files2process: List[Path] = self.get_files2process()

    def run(self) -> None:
        self.exit_if_nothing_to_process(self.files2process)

        if not self.skip_preview:
            print("Preview:")
            delete_files(files2process=self.files2process, dry_run=True)
            if not user_query(
                'If you want to delete for real, give me a "yes" or "y" now!'
            ):
                print("Will not delete for now. See you soon.")
                sys.exit(0)
        delete_files(files2process=self.files2process, dry_run=False)
