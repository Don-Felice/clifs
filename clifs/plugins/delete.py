"""Clifs plugin for file deletion"""

import sys
from argparse import ArgumentParser, Namespace

from clifs import ClifsPlugin
from clifs.utils_cli import CONSOLE, cli_bar, print_line, user_query
from clifs.utils_fs import PathGetterMixin


class FileDeleter(ClifsPlugin, PathGetterMixin):
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

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.console = CONSOLE
        self.files2process, _ = self.get_paths()

    def run(self) -> None:
        self.exit_if_nothing_to_process(self.files2process)

        if not self.skip_preview:
            self.console.print("Preview:")
            self.delete_files(dry_run=True)
            if not user_query(
                'If you want to delete for real, give me a "yes" or "y" now!'
            ):
                print("Will not delete for now. See you soon.")
                sys.exit(0)
        self.delete_files(dry_run=False)

    def delete_files(self, dry_run: bool = False) -> None:
        num_files2process = len(self.files2process)
        print_line(self.console)
        if dry_run:
            self.console.print(f"Would delete the following {num_files2process} files:")
        else:
            self.console.print(f"Deleting {num_files2process} files:")

        num_file = 0
        for num_file, path_file in enumerate(self.files2process, 1):
            if dry_run:
                self.console.print(f"    {path_file.name}")
            else:
                path_file.unlink(missing_ok=True)
                cli_bar(
                    num_file,
                    num_files2process,
                    suffix=f"deleted. Last: {path_file.name}",
                )
        print_line(self.console)
        if not dry_run:
            print(f"Hurray, {num_file} files have been deleted.")
