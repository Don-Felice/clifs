"""Clifs plugins for file copying and moving"""

import shutil
import sys
from abc import ABC
from argparse import ArgumentParser, Namespace
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, NamedTuple

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


class OperationVerbs(NamedTuple):
    """Verbs describing the file operation to place in cli logs
    E.g. ('copy', 'copied', copying)"""

    verb: str
    past: str
    present: str


class CoMo(ClifsPlugin, PathGetterMixin, ABC):  # pylint: disable=too-many-instance-attributes
    """
    Base class to copy or move files.

    """

    files2process: list[Path]
    dir_dest: Path
    skip_existing: bool
    keep_all: bool
    flatten: bool
    terse: bool
    dryrun: bool

    # this needs to be implemented in all sub-classes
    operation: Callable[[Path, Path], Any]  # pylint: disable=method-hidden
    # this needs to be implemented in all sub-classes
    op_description: ClassVar[OperationVerbs]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for attribute in ["operation", "op_description"]:
            if not hasattr(cls, attribute):
                msg = f"Attribute '{attribute}' not implemented."
                raise NotImplementedError(msg)

    @classmethod
    def init_parser(cls, parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)

        parser.add_argument(
            "dir_dest",
            type=Path,
            help=f"Folder to {cls.op_description.verb} files to.",
        )
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
        self.dir_source = self.dir_source.absolute()
        self.dir_target = self.dir_dest.absolute()

        if self.dryrun:
            self.operation = lambda x, y: ...

        self.get_path_dest = self.get_path_dest_getting_method()
        self.process_file = self.get_file_processing_method()
        self.create_file = self.get_file_creation_method()

        self.files2process, _ = self.get_paths()

        # define progress
        self.progress: dict[str, Progress] = {
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
        self.dir_dest.parent.mkdir(exist_ok=True, parents=True)
        self.como()

    def get_tasks(self) -> dict[str, TaskID]:
        # define overall progress task
        tasks = {
            "progress": self.progress["overall"].add_task(
                f"{self.op_description.present.title()} data:  ",
                total=len(self.files2process),
                last_action="-",
            ),
        }

        # define counter tasks
        tasks[f"files_{self.op_description.past}"] = self.progress["counts"].add_task(
            f"Files {self.op_description.past}:", total=None
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

    def get_path_dest_getting_method(
        self,
    ) -> Callable[[Path], Path]:
        if self.flatten:
            return self.get_path_dest_flat
        return self.get_path_dest_deep

    def get_path_dest_flat(self, path_file: Path) -> Path:
        return self.dir_dest / path_file.name

    def get_path_dest_deep(self, path_file: Path) -> Path:
        return self.dir_dest / path_file.relative_to(self.dir_source)

    def get_file_creation_method(self) -> Callable[[Path, Path], None]:
        if self.flatten:
            return self.create_file_flat
        return self.create_file_deep

    def create_file_flat(self, file_src: Path, file_dest: Path) -> None:
        self.operation(file_src, file_dest)
        self.progress["counts"].advance(self.tasks[f"files_{self.op_description.past}"])

    def create_file_deep(self, file_src: Path, file_dest: Path) -> None:
        if not self.dryrun:
            file_dest.parent.mkdir(exist_ok=True, parents=True)
        self.create_file_flat(file_src, file_dest)

    def get_file_processing_method(self) -> Callable[[Path, Path], str | None]:
        if self.skip_existing and self.keep_all:
            self.console.print(
                "You can only choose to either skip existing files "
                "or keep both versions. Choose wisely!"
            )
            sys.exit(0)
        if self.keep_all:
            return self.process_file_keep_all
        if self.skip_existing:
            return self.process_file_skip_existing
        return self.process_file_replace_existing

    def process_file_skip_existing(self, path_src: Path, path_dest: Path) -> str | None:
        report = None
        if path_dest.exists():
            report = set_style(
                f"Skipped as already present: {path_src.name}",
                "warning",
            )
            self.progress["counts"].advance(self.tasks["files_skipped"])
            return report
        self.create_file(path_src, path_dest)
        return report

    def process_file_keep_all(self, path_src: Path, path_dest: Path) -> str | None:
        report = None
        if path_dest.exists():
            path_dest_new = get_unique_path(path_dest)
            if path_dest_new != path_dest:
                report = set_style(
                    "Changed name as already present: "
                    f"{path_dest.name} -> {path_dest_new.name}",
                    "warning",
                )
                path_dest = path_dest_new
                self.progress["counts"].advance(self.tasks["files_renamed"])
        self.create_file(path_src, path_dest)
        return report

    def process_file_replace_existing(
        self, path_src: Path, path_dest: Path
    ) -> str | None:
        report = None
        if path_dest.exists():
            report = set_style(
                f"Replacing existing version for: {path_src.name}",
                "warning",
            )
            self.progress["counts"].advance(self.tasks["files_replaced"])
        self.create_file(path_src, path_dest)
        return report

    def como(self) -> None:
        print_line(self.console)
        if self.dryrun:
            print("Dry run:\n")
        self.console.print(
            f"{self.op_description.present} {len(self.files2process)} files\n"
            f"from: {self.dir_source}\n"
            f"to:   {self.dir_dest}"
        )

        with Live(
            self.progress_table,
            console=self.console,
            auto_refresh=False,
        ) as live:
            for num_file, file_src in enumerate(self.files2process, 1):
                file_dest = self.get_path_dest(file_src)
                process_report = self.process_file(file_src, file_dest)
                file_report = (
                    f"Last: {file_src.name}"
                    if process_report is None
                    else process_report
                )

                if not self.terse:
                    cli_bar(
                        num_file,
                        len(self.files2process),
                        suffix=f"{self.op_description.past}. {file_report}",
                        console=self.console,
                    )
                self.progress["overall"].update(
                    self.tasks["progress"],
                    last_action=f"{self.op_description.past} {file_src.name}",
                )
                self.progress["overall"].advance(self.tasks["progress"])
                live.refresh()
        print_line(self.console)


class FileMover(CoMo):
    """
    Move files
    """

    plugin_description = """Move files from one location to the other.
     Supports multiple ways to select files and to deal with files already existing at
     the target location."""

    operation = staticmethod(shutil.move)
    op_description = OperationVerbs(verb="move", past="moved", present="moving")


class FileCopier(CoMo):
    """
    Copy files
    """

    plugin_description = """Copy files from one location to the other.
     Supports multiple ways to select files and to deal with files already existing at
     the target location."""

    operation = staticmethod(shutil.copy2)
    op_description = OperationVerbs(verb="copy", past="copied", present="copying")
