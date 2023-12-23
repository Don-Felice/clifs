"""Clifs plugins for file copying and moving"""

import shutil
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Dict, List

from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table

from clifs import ClifsPlugin
from clifs.utils_cli import (
    cli_bar,
    get_count_progress,
    get_last_action_progress,
    print_line,
    set_style,
)
from clifs.utils_fs import PathGetterMixin, get_unique_path


class CoMo(ClifsPlugin, PathGetterMixin):
    """
    Base class to copy or move files.

    """

    files2process: List[Path]
    dir_dest: Path
    skip_existing: bool
    keep_all: bool
    flatten: bool
    terse: bool
    dryrun: bool
    move: bool

    @classmethod
    def init_parser(cls, parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)

        parser.add_argument("dir_dest", type=Path, help="Folder to copy/move files to")
        parser.add_argument(
            "-se",
            "--skip_existing",
            action="store_true",
            help="Do nothing if file already exists in destination "
            "(instead of replacing).",
        )
        parser.add_argument(
            "-ka",
            "--keep_all",
            action="store_true",
            help="Keep both versions if a file already exists in destination "
            "(instead of replacing).",
        )
        parser.add_argument(
            "-flt",
            "--flatten",
            action="store_true",
            help="Flatten folder structure in output directory when running "
            "in recursive mode. "
            "Be careful with files of identical name in different subfolders as "
            "they will overwrite each other by default!",
        )
        parser.add_argument(
            "-t", "--terse", action="store_true", help="Report the summary only."
        )
        parser.add_argument(
            "-dr", "--dryrun", action="store_true", help="Don't touch anything"
        )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)

        if self.skip_existing and self.keep_all:
            self.console.print(
                "You can only choose to either skip existing files "
                "or keep both versions. Choose wisely!"
            )
            sys.exit(0)

        self.files2process, _ = self.get_paths()

        # define progress
        self.progress: Dict[str, Progress] = {
            "counts": get_count_progress(),
            "overall": get_last_action_progress(),
        }
        self.action = "Moving" if self.move else "Copying"
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
        self.dir_dest.parent.mkdir(exist_ok=True, parents=True)
        self.como()

    def get_tasks(self) -> Dict[str, TaskID]:
        # define overall progress task
        tasks = {
            "progress": self.progress["overall"].add_task(
                f"{self.action} data:  ", total=len(self.files2process), last_action="-"
            ),
        }

        # define counter tasks
        if self.move:
            tasks["files_moved"] = self.progress["counts"].add_task(
                "Files moved:", total=None
            )
        else:
            tasks["files_copied"] = self.progress["counts"].add_task(
                "Files copied:", total=None
            )

        if self.skip_existing:
            tasks["files_skipped"] = self.progress["counts"].add_task(
                "Files skipped:", total=None
            )
        elif self.keep_all:
            tasks["files_renamed"] = self.progress["counts"].add_task(
                "Files renamed:", total=None
            )
        else:
            tasks["files_replaced"] = self.progress["counts"].add_task(
                "Files replaced:", total=None
            )
        return tasks

    def create_file(self, file_src: Path, file_dest: Path) -> None:
        if not self.flatten and not self.dryrun:
            file_dest.parent.mkdir(exist_ok=True, parents=True)
        if self.move:
            if not self.dryrun:
                shutil.move(str(file_src), str(file_dest))
            self.progress["counts"].advance(self.tasks["files_moved"])
        else:
            if not self.dryrun:
                shutil.copy2(str(file_src), str(file_dest))
            self.progress["counts"].advance(self.tasks["files_copied"])

    def como(self) -> None:
        print_line(self.console)
        if self.dryrun:
            print("Dry run:\n")
        self.console.print(
            f"{self.action} {len(self.files2process)} files\n"
            f"from: {self.dir_source}\n"
            f"to:   {self.dir_dest}"
        )

        with Live(
            self.progress_table,
            console=self.console,
            auto_refresh=False,
        ) as live:
            for num_file, file in enumerate(self.files2process, 1):
                skip = False
                txt_report = f"Last: {file.name}"
                filepath_dest = self.get_path_dest(file)
                if filepath_dest.exists():
                    if self.skip_existing:
                        txt_report = set_style(
                            f"Skipped as already present: " f"{file.name}",
                            "warning",
                        )
                        skip = True
                        self.progress["counts"].advance(self.tasks["files_skipped"])
                    elif self.keep_all:
                        filepath_dest_new = get_unique_path(filepath_dest)
                        if filepath_dest_new != filepath_dest:
                            txt_report = set_style(
                                "Changed name as already present: "
                                f"{filepath_dest.name} -> {filepath_dest_new.name}",
                                "warning",
                            )
                            filepath_dest = filepath_dest_new
                            self.progress["counts"].advance(self.tasks["files_renamed"])
                    else:
                        txt_report = set_style(
                            f"Replacing existing version for: {file.name}",
                            "warning",
                        )
                        self.progress["counts"].advance(self.tasks["files_replaced"])

                if not skip:
                    self.create_file(file, filepath_dest)

                last_action = "moved" if self.move else "copied"
                if not self.terse:
                    cli_bar(
                        num_file,
                        len(self.files2process),
                        suffix=f"{last_action}. {txt_report}",
                        console=self.console,
                    )
                self.progress["overall"].update(
                    self.tasks["progress"],
                    last_action=f"{last_action} {file.name}",
                )
                self.progress["overall"].advance(self.tasks["progress"])
                live.refresh()
        print_line(self.console)

    def get_path_dest(self, path_file: Path) -> Path:
        if self.flatten:
            return self.dir_dest / path_file.name
        return Path(str(path_file).replace(str(self.dir_source), str(self.dir_dest)))


class FileMover(CoMo):
    """
    Move files
    """

    def __init__(self, args: Namespace) -> None:
        self.move = True
        super().__init__(args)


class FileCopier(CoMo):
    """
    Copy files
    """

    def __init__(self, args: Namespace) -> None:
        self.move = False
        super().__init__(args)
