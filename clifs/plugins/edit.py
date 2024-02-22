"""Clifs plugin to edit text files"""

import re
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Dict, List, Optional, Union

from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table

from clifs import ClifsPlugin
from clifs.utils_cli import (
    MatchHighlighter,
    get_count_progress,
    get_last_action_progress,
    print_line,
    set_style,
    user_query,
)
from clifs.utils_fs import PathGetterMixin, get_unique_path

IO_ERROR_MESSAGE = set_style(
    "Could not read or modify the following file, check that "
    "it is a text file readable with the chosen encoding "
    "'{encoding}' and you have read/write access:\n{file_path}"
)


class StreamingEditor(ClifsPlugin, PathGetterMixin):
    """
    Base class to copy or move files.

    """

    files2process: List[Path]
    dir_dest: Path
    dryrun: bool
    encoding: str
    lines: str
    pattern: str
    replacement: str
    max_previews: int
    dont_overwrite: bool

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
            "(https://docs.python.org/3/library/re.html). "
            "Note that e.g. a pattern like '.*[\r\n]+' can be used in combination with "
            "an empty replacement to delete the selected lines. "
            "A pattern like '[\r\n]+' in combination with a replacement like "
            "'\ninsert\nlines\n' can be used to append lines to specific lines.",
        )
        parser.add_argument(
            "-rp",
            "--replacement",
            default="",
            help="String to use as replacement. "
            "You can use \\1 \\2 etc. to refer to matching groups.",
        )
        parser.add_argument(
            "-l",
            "--lines",
            type=str,
            help="Lines to edit. If not given all lines are processed. "
            "Supports ranges by giving two integers separated by a hyphen (e.g.'1-5') "
            "or lists of lines given by comma separated integer (e.g. '3,4,10'). ",
        )
        parser.add_argument(
            "-e",
            "--encoding",
            type=str,
            default="utf-8",
            help="Text file encoding.",
        )
        parser.add_argument(
            "-do",
            "--dont_overwrite",
            action="store_true",
            help="Do not overwrite the input file but create a second file "
            "including the suffix '_edited' next to each input file.",
        )
        parser.add_argument(
            "-mp",
            "--max_previews",
            type=int,
            default=5,
            help="Maximum number of line changes shown in the preview mode. "
            "Set to zero to skip preview mode completely. Only for the brave...",
        )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

        self.files2process, _ = self.get_paths()
        self.line_nums = self.parse_line_nums()

        self.highlight_match = MatchHighlighter(pattern=self.pattern)

        self.preview_count = 0

        # define progress
        self.progress: Dict[str, Progress] = {
            "counts": get_count_progress(),
            "overall": get_last_action_progress(),
        }
        self.tasks = self.get_tasks()

        self.progress_table = Table.grid()
        self.progress_table.add_row(
            Panel.fit(
                self.progress["overall"],
                title="Progress",
                border_style="cyan",
                padding=(1, 2),
            ),
            Panel.fit(
                self.progress["counts"],
                title="Counts",
                border_style="bright_black",
                padding=(1, 2),
            ),
        )

    def run(self) -> None:
        self.exit_if_nothing_to_process(self.files2process)
        if self.max_previews > 0:
            print_line(self.console, title="PREVIEW")
            for file in self.files2process:
                try:
                    self.preview_replace(file)
                except (IOError, UnicodeDecodeError):
                    self.console.print(
                        IO_ERROR_MESSAGE.format(encoding=self.encoding, file_path=file)
                    )
                    sys.exit(1)
                if self.preview_count >= self.max_previews:
                    break
            print_line(self.console, title="END OF PREVIEW")
            if not user_query(
                'If you want to apply the edits, give me a "yes" or "y" now!'
            ):
                self.console.print("Will not edit files for now. See you soon.")
                sys.exit(0)
        with Live(
            self.progress_table,
            console=self.console,
            auto_refresh=False,
        ) as live:
            for file in self.files2process:
                try:
                    self.replace(file)
                    self.progress["overall"].update(
                        self.tasks["progress"],
                        last_action=f"edited '{file.name}'",
                    )
                    self.progress["overall"].advance(self.tasks["progress"])
                    self.progress["counts"].advance(self.tasks["files_edited"])
                    live.refresh()
                except (IOError, UnicodeDecodeError):
                    self.console.print(
                        IO_ERROR_MESSAGE.format(encoding=self.encoding, file_path=file)
                    )
                    sys.exit(1)

    def parse_line_nums(self) -> Optional[Union[List[int], range]]:
        line_nums: Optional[Union[List[int], range]]
        try:
            if self.lines is None:
                return None
            if "-" in self.lines:
                range_min, range_max = map(int, self.lines.split("-"))
                line_nums = range(range_min, range_max + 1)
            elif "," in self.lines:
                line_nums = list(map(int, self.lines.split(",")))

            else:
                line_nums = [int(self.lines)]

        except ValueError:
            self.console.print(
                set_style(
                    f"Could not parse line input: '{self.lines}'. "
                    "Expecting line numbers >=0 given as either a single integer, "
                    "comma separated list of integers, or a range given in format "
                    "'min_line-max_line'.",
                    "error",
                )
            )
            sys.exit(1)

        if min(line_nums) < 1:
            self.console.print(
                set_style(
                    f"Line input contains numbers smaller than one: '{self.lines}'. "
                    "Please select lines >=1 only.",
                    "error",
                )
            )
            sys.exit(1)
        return line_nums

    def get_tasks(self) -> Dict[str, TaskID]:
        # define overall progress task
        tasks = {
            "progress": self.progress["overall"].add_task(
                "Editing files: ", total=len(self.files2process), last_action="-"
            ),
        }

        # define counter tasks
        tasks["files_edited"] = self.progress["counts"].add_task(
            "Files edited:", total=None
        )
        tasks["lines_changed_total"] = self.progress["counts"].add_task(
            "Lines modified:", total=None
        )
        return tasks

    def preview_replace(self, input_file: Path) -> None:
        self.console.print(
            f"Changes in file '{input_file.name}': "
            + set_style(f"(at: {input_file.parent})", "bright_black")
        )
        file_change_count = 0
        with input_file.open("r", encoding=self.encoding) as input_fh:
            if self.line_nums is None:
                for line_num, line in enumerate(input_fh, 1):
                    if self.preview_count < self.max_previews:
                        mod_line = re.sub(self.pattern, self.replacement, line)
                        if mod_line != line:
                            self.preview_count += 1
                            file_change_count += 1
                            self.print_line_diff(line, mod_line, line_num)
                    else:
                        break
            else:
                for line_num, line in enumerate(input_fh, 1):
                    if self.preview_count < self.max_previews:
                        if line_num in self.line_nums:
                            mod_line = re.sub(self.pattern, self.replacement, line)
                            if mod_line != line:
                                self.preview_count += 1
                                file_change_count += 1
                                self.print_line_diff(line, mod_line, line_num)
                    else:
                        break
            if file_change_count == 0:
                self.console.print("  ----")

    def print_line_diff(self, line: str, mod_line: str, line_num: int) -> None:
        self.console.print(
            f"  l{line_num} old:", self.highlight_match(line.rstrip("\n"))
        )
        self.console.print(f"  l{line_num} new:", mod_line.rstrip("\n"))
        self.console.print()

    def replace(self, input_file: Path) -> None:
        """
        Replace all occurrences of a regex pattern in text file specified replacement.

        We read/write line by line here to avoid memory issues for large files.

        :param input_file: The path to the input text file.
        :return: None
        """

        temp_output_file = get_unique_path(
            input_file.parent / (input_file.stem + "_edited" + input_file.suffix)
        )

        with input_file.open(
            "r", encoding=self.encoding
        ) as input_fh, temp_output_file.open("w", encoding=self.encoding) as output_fh:
            if self.line_nums is None:
                for line_num, line in enumerate(input_fh, 1):
                    mod_line = re.sub(self.pattern, self.replacement, line)
                    if mod_line != line:
                        self.progress["counts"].advance(
                            self.tasks["lines_changed_total"]
                        )
                    output_fh.write(mod_line)
            else:
                for line_num, line in enumerate(input_fh, 1):
                    if line_num in self.line_nums:
                        mod_line = re.sub(self.pattern, self.replacement, line)
                        if mod_line != line:
                            self.progress["counts"].advance(
                                self.tasks["lines_changed_total"]
                            )
                        output_fh.write(mod_line)
                    else:
                        output_fh.write(line)

        if not self.dont_overwrite:
            input_file.unlink()
            temp_output_file.rename(input_file)
