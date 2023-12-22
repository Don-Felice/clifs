"""Clifs plugin for regex-based renaming of files and folders"""

import re
import sys
from argparse import ArgumentParser, Namespace

# from collections import Counter
from pathlib import Path
from typing import Counter, List, Literal, Set

from clifs import ClifsPlugin
from clifs.utils_cli import cli_bar, print_line, set_style, user_query
from clifs.utils_fs import INDENT, PathGetterMixin, get_unique_path


class Renamer(ClifsPlugin, PathGetterMixin):
    """
    Regex-based renaming of files and folders.
    """

    pattern: str
    replacement: str
    rename_dirs: bool
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
            "-d",
            "--dirs",
            dest="rename_dirs",
            action="store_true",
            help="Rename directories instead of files.",
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

        self.counter: Counter[str] = Counter()
        self.files, self.dirs = self.get_paths()
        if self.rename_dirs:
            # process deeper folders first to avoid changing paths on the fly
            self.dirs = self.sort_paths(self.dirs)

    def run(self) -> None:
        if not self.rename_dirs:
            if not self.files:
                self.console.print("No files to process")
            else:
                if not self.skip_preview:
                    self.rename(self.files, path_type="files", preview_mode=True)
                    if not user_query(
                        'If you want to apply renaming, give me a "yes" or "y" now!'
                    ):
                        self.console.print("Will not rename for now. See you soon.")
                        sys.exit(0)
                self.rename(self.files, path_type="files", preview_mode=False)
        else:
            if not self.dirs:
                self.console.print("No dirs to process")
            else:
                if not self.skip_preview:
                    self.rename(self.dirs, path_type="dirs", preview_mode=True)
                    if not user_query(
                        'If you want to apply renaming, give me a "yes" or "y" now!'
                    ):
                        self.console.print("Will not rename for now. See you soon.")
                        sys.exit(0)
                self.rename(self.dirs, path_type="dirs", preview_mode=False)

    def rename(
        self,
        paths: List[Path],
        path_type: Literal["files", "dirs"],
        preview_mode: bool = True,
    ) -> None:
        self.counter.clear()
        self.counter["paths_total"] = len(paths)

        self.console.print(f"Renaming {self.counter['paths_total']} {path_type}.")
        print_line(self.console)
        paths_to_be_added: Set[Path] = set()
        paths_to_be_deleted: Set[Path] = set()
        if preview_mode:
            self.console.print("Preview:")

        num_path = 0
        for num_path, path in enumerate(paths, 1):
            name_old = path.name
            name_new = re.sub(self.pattern, self.replacement, name_old)
            message_rename = f"{name_old:35} -> {name_new:35}"

            # skip items if renaming would result in bad characters
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
                    num_path,
                    preview_mode=preview_mode,
                )
                continue

            # make sure resulting paths are unique
            path_new = path.parent / name_new
            path_unique = get_unique_path(
                path_new,
                set_taken=paths_to_be_added,
                set_free=paths_to_be_deleted | {path},
            )

            if path_new != path_unique:
                path_new = path_unique
                name_new = path_unique.name
                message_rename = f"{name_old:35} -> {name_new:35}"
                message_rename += set_style(
                    f"{INDENT}Warning: name already exists. Adding number suffix.",
                    "warning",
                )
                self.counter["name_conflicts"] += 1

            # skip items that are not renamed
            if path_new == path:
                message_rename = set_style(message_rename, "bright_black")
                self.print_rename_message(
                    message_rename,
                    num_path,
                    preview_mode=preview_mode,
                )
                continue

            self.print_rename_message(
                message_rename,
                num_path,
                preview_mode=preview_mode,
            )
            if not preview_mode:
                path.rename(path_new)
                self.counter["paths_renamed"] += 1
            else:
                paths_to_be_added.add(path_new)
                if path_new in paths_to_be_deleted:
                    paths_to_be_deleted.remove(path_new)
                paths_to_be_deleted.add(path)

        if self.counter["bad_results"] > 0:
            self.console.print(
                set_style(
                    f"Warning: {self.counter['bad_results']} out of "
                    f"{self.counter['paths_total']} files not renamed as it would "
                    "result in bad characters.",
                    "warning",
                )
            )

        if self.counter["name_conflicts"] > 0:
            self.console.print(
                set_style(
                    f"Warning: {self.counter['name_conflicts']} out of "
                    f"{self.counter['paths_total']} renamings would have resulted in "
                    "name conflicts. Added numbering suffixes to get unique names.",
                    "warning",
                )
            )

        if not preview_mode:
            self.console.print(
                f"Hurray, {num_path} {path_type} have been processed, "
                f"{self.counter['paths_renamed']} have been renamed."
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
                self.counter["paths_total"],
                suffix=space_prefix + message,
                console=self.console,
            )

    @staticmethod
    def find_bad_char(string: str) -> List[str]:
        """Check stings for characters causing problems in windows file system."""
        bad_chars = r"~“#%&*:<>?/\{|}"
        return [x for x in bad_chars if x in string]
