"""Clifs plugin for regex-based renaming of files and folders"""

import re
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Counter, List, Literal, Set

from rich.text import Text

from clifs import ClifsPlugin
from clifs.utils_cli import MatchHighlighter, cli_bar, print_line, set_style, user_query
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
            "with a replacement like '\\1_suffix.\\2' will append suffixes.",
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
        self.highlight_match = MatchHighlighter(pattern=self.pattern)

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
        paths_to_be_added: Set[Path] = set()
        paths_to_be_deleted: Set[Path] = set()
        if preview_mode:
            print_line(self.console, "PREVIEW")

        num_path = 0
        for num_path, path in enumerate(paths, 1):
            name_old = path.name
            name_new = re.sub(self.pattern, self.replacement, name_old)
            messages: List[Text] = []

            # skip items if renaming would result in bad characters
            found_bad_chars = self.find_bad_char(name_new)
            if found_bad_chars:
                messages.append(
                    Text(
                        f"{INDENT}Error: not doing renaming as it would result "
                        f"in invalid characters: '{','.join(found_bad_chars)}'",
                        style="error",
                    )
                )
                self.counter["bad_results"] += 1
                self.print_rename_message(
                    name_old,
                    name_new,
                    num_path,
                    add_messages=messages,
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
                messages.append(
                    Text(
                        f"{INDENT}Warning: name already exists. Adding number suffix.",
                        style="warning",
                    )
                )
                self.counter["name_conflicts"] += 1

            self.print_rename_message(
                name_old,
                name_new,
                num_path,
                add_messages=messages,
                preview_mode=preview_mode,
            )
            # skip items that are not renamed
            if path_new == path:
                continue

            if not preview_mode:
                path.rename(path_new)
                self.counter["paths_renamed"] += 1
            else:
                paths_to_be_added.add(path_new)
                if path_new in paths_to_be_deleted:
                    paths_to_be_deleted.remove(path_new)
                paths_to_be_deleted.add(path)

        if self.counter["bad_results"] > 0:
            noun = "item" if self.counter["name_conflicts"] == 1 else "items"
            self.console.print(
                set_style(
                    f"Warning: {self.counter['bad_results']} {noun} not renamed, "
                    "as it would result in invalid characters.",
                    "warning",
                )
            )

        if self.counter["name_conflicts"] > 0:
            noun = "change" if self.counter["name_conflicts"] == 1 else "changes"
            self.console.print(
                set_style(
                    f"Warning: {self.counter['name_conflicts']} {noun} would have "
                    "resulted in name conflicts. "
                    "Added number suffixes to get unique names.",
                    "warning",
                )
            )

        if not preview_mode:
            self.console.print(
                f"Hurray, {num_path} {path_type} have been processed, "
                f"{self.counter['paths_renamed']} have been renamed."
            )
        if preview_mode:
            print_line(self.console, "END OF PREVIEW")

    def print_rename_message(  # pylint: disable=too-many-arguments
        self,
        name_old: str,
        name_new: str,
        num_path: int,
        add_messages: List[Text],
        preview_mode: bool = False,
    ) -> None:
        indent = 2
        padding = 35

        if name_new == name_old:
            print_message = Text(
                f"{name_old:{padding}} -> {name_new:{padding}}", style="bright_black"
            )
        else:
            highlight_old_name = self.highlight_match(name_old)
            highlight_old_name.pad_right(padding - len(name_old))
            print_message = highlight_old_name + Text(f" -> {name_new:{padding}}")

        for add_mes in add_messages:
            add_mes.pad_left(1)
            print_message += add_mes
        print_message.pad_left(indent)

        if preview_mode:
            self.console.print(print_message)
        else:
            cli_bar(
                num_path,
                self.counter["paths_total"],
                suffix=print_message,
                console=self.console,
            )

    @staticmethod
    def find_bad_char(string: str) -> List[str]:
        """Check stings for characters causing problems in Windows file system."""
        bad_chars = r"~“#%&*:<>?/\{|}"
        return [x for x in bad_chars if x in string]
