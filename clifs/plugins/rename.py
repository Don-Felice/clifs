# -*- coding: utf-8 -*-

import re
import sys
from argparse import ArgumentParser, Namespace
from collections import Counter
from pathlib import Path
from typing import List, Set

from clifs import ClifsPlugin
from clifs.utils_cli import cli_bar, print_line, set_style, user_query
from clifs.utils_fs import INDENT, FileGetterMixin, get_unique_path


class FileRenamer(ClifsPlugin, FileGetterMixin):
    """
    Regex-based file renaming.
    """

    pattern: str
    replacement: str
    skip_preview: bool

    @classmethod
    def init_parser(cls, parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)

        parser.add_argument(
            "-pt",
            "--pattern",
            default=".*",
            help="Pattern identifying the substring to be replaced. "
            "Supports syntax for `re.sub` from regex module "
            "(https://docs.python.org/3/library/re.html).",
        )
        parser.add_argument(
            "-rp",
            "--replacement",
            default="",
            help="String to use as replacement. "
            "You can use \\1 \\2 etc. to refer to matching groups. "
            "E.g. a pattern like '(.+)\\.(.+)' in combination "
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

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.files2process: List[Path] = self.get_files()
        self.counter = Counter(files2process=len(self.files2process))

    def run(self) -> None:
        self.exit_if_nothing_to_process(self.files2process)

        if not self.skip_preview:
            self.rename_files(preview_mode=True)
            if not user_query(
                'If you want to apply renaming, give me a "yes" or "y" now!'
            ):
                self.console.print("Will not rename for now. See you soon.")
                sys.exit(0)

        self.rename_files(preview_mode=False)

    def rename_files(
        self,
        preview_mode: bool = True,
    ) -> None:
        self.console.print(f"Renaming {self.counter['files2process']} files.")
        print_line(self.console)
        files_to_be_added: Set[Path] = set()
        files_to_be_deleted: Set[Path] = set()
        if preview_mode:
            self.console.print("Preview:")

        num_file = 0
        for num_file, path_file in enumerate(self.files2process, 1):
            name_old = path_file.name
            name_new = re.sub(self.pattern, self.replacement, name_old)
            message_rename = f"{name_old:35} -> {name_new:35}"

            # skip files if renaming would result in bad characters
            found_bad_chars = self.find_bad_char(name_new)
            if found_bad_chars:
                message_rename += set_style(
                    f"{INDENT}Error: not doing renaming as it would result "
                    f"in bad characters: '{','.join(found_bad_chars)}'",
                    "error",
                )
                self.counter["bad_results"] += 1
                self.print_rename_message(
                    message_rename,
                    num_file,
                    preview_mode=preview_mode,
                )
                continue

            # make sure resulting paths are unique
            path_file_new = path_file.parent / name_new
            path_file_unique = get_unique_path(
                path_file_new,
                set_taken=files_to_be_added,
                set_free=files_to_be_deleted | {path_file},
            )

            if path_file_new != path_file_unique:
                path_file_new = path_file_unique
                name_new = path_file_unique.name
                message_rename = f"{name_old:35} -> {name_new:35}"
                message_rename += set_style(
                    f"{INDENT}Warning: name result would already exist. "
                    "Adding number suffix.",
                    "warning",
                )
                self.counter["name_conflicts"] += 1

            # skip files that are not renamed
            if path_file_new == path_file:
                message_rename = set_style(message_rename, "bright_black")
                self.print_rename_message(
                    message_rename,
                    num_file,
                    preview_mode=preview_mode,
                )
                continue

            self.print_rename_message(
                message_rename,
                num_file,
                preview_mode=preview_mode,
            )
            if not preview_mode:
                path_file.rename(path_file_new)
                self.counter["files_renamed"] += 1
            else:
                files_to_be_added.add(path_file_new)
                if path_file_new in files_to_be_deleted:
                    files_to_be_deleted.remove(path_file_new)
                files_to_be_deleted.add(path_file)

        if self.counter["bad_results"] > 0:
            self.console.print(
                set_style(
                    f"Warning: {self.counter['bad_results']} out of "
                    f"{self.counter['files2process']} files not renamed as it would "
                    "result in bad characters.",
                    "warning",
                )
            )

        if self.counter["name_conflicts"] > 0:
            self.console.print(
                set_style(
                    f"Warning: {self.counter['name_conflicts']} out of "
                    f"{self.counter['files2process']} renamings would have resulted in "
                    "name conflicts. Added numbering suffices to get unique names.",
                    "warning",
                )
            )

        if not preview_mode:
            self.console.print(
                f"Hurray, {num_file} files have been processed, "
                f"{self.counter['files_renamed']} have been renamed."
            )
        print_line(self.console)

    def print_rename_message(
        self,
        message: str,
        num_file: int,
        preview_mode: bool = False,
        space_prefix: str = "    ",
    ) -> None:
        if preview_mode:
            self.console.print(space_prefix + message)
        else:
            cli_bar(
                num_file,
                self.counter["files2process"],
                suffix=space_prefix + message,
                console=self.console,
            )

    @staticmethod
    def find_bad_char(string: str) -> List[str]:
        """Check stings for characters causing problems in windows file system."""
        bad_chars = r"~“#%&*:<>?/\{|}"
        return [x for x in bad_chars if x in string]
