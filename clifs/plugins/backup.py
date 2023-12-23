"""Clifs plugin to create data backups"""

import csv
import shutil
import sys
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table

from clifs import ClifsPlugin
from clifs.utils_cli import (
    CONSOLE,
    get_count_progress,
    get_last_action_progress,
    print_line,
    set_style,
)


class DirPair(NamedTuple):
    """Source/Destination directory pair"""

    source: Path
    dest: Path


def conditional_copy(
    path_source: Path, path_dest: Path, dry_run: bool = False
) -> Optional[str]:
    """
    Copy only if dest file does not exist or is older than the source file.
    """
    process = None
    if not path_dest.exists():
        process = "adding"
    elif (path_source.stat().st_mtime - path_dest.stat().st_mtime) > 1:
        process = "updating"

    if process is not None and not dry_run:
        path_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path_source, path_dest)
    return process


def conditional_delete(
    path_source: Path, path_dest: Path, list_source: List[Path], dry_run: bool = False
) -> int:
    """
    Delete only if `path_source` is not in `list_source`.
    """
    if path_source not in list_source and path_dest.exists():
        if path_dest.is_dir():
            if not dry_run:
                shutil.rmtree(str(path_dest))
        else:
            if not dry_run:
                path_dest.unlink()
        return 1
    return 0


def list_filedirs(dir_source: Path) -> Tuple[List[Path], List[Path]]:
    """
    List files and directories in a source dir.
    """

    list_files = []
    list_dirs = []

    for cur_file in dir_source.rglob("*"):
        if cur_file.is_dir():
            list_dirs.append(cur_file)
        else:
            list_files.append(cur_file)

    return list_files, list_dirs


class FileSaver(ClifsPlugin):
    """
    Create backups from folders.
    """

    dir_source: Optional[Path]
    dir_dest: Optional[Path]
    cfg_file: Optional[Path]
    delete: bool
    verbose: bool
    dry_run: bool

    @staticmethod
    def init_parser(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs plugins.
        """

        parser.add_argument(
            "-s", "--dir_source", type=Path, default=None, help="Source directory"
        )
        parser.add_argument(
            "-d", "--dir_dest", type=Path, default=None, help="Destination directory"
        )
        parser.add_argument(
            "-cfg",
            "--cfg_file",
            type=Path,
            default=None,
            help="Path to the config file",
        )
        parser.add_argument(
            "-del",
            "--delete",
            action="store_true",
            default=False,
            help=(
                "Delete files which exist in destination directory but not in "
                "the source directory"
            ),
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=False,
            help="Report on every action to stdout.",
        )
        parser.add_argument(
            "-dr",
            "--dry_run",
            action="store_true",
            default=False,
            help="Do not touch anything.",
        )

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self.console = CONSOLE

        if self.cfg_file and self.dir_source or self.cfg_file and self.dir_dest:
            self.console.print(
                "Paths provided in config table and as parameters. "
                "You'll have to decide for one option I am afraid."
            )
            sys.exit(0)

        if self.cfg_file:
            # TODO: check_cfg_format(cfg_file)  # pylint: disable=fixme
            self.dir_pairs = []
            with self.cfg_file.open(newline="\n", encoding="utf-8") as cfg_file:
                reader = csv.DictReader(cfg_file, fieldnames=["source_dir", "dest_dir"])
                # skip header row
                next(reader)
                for row in reader:
                    self.dir_pairs.append(
                        DirPair(Path(row["source_dir"]), Path(row["dest_dir"]))
                    )

        elif self.dir_source and self.dir_dest:
            self.dir_pairs = [DirPair(self.dir_source, self.dir_dest)]

    def run(self) -> None:
        """
        Running the plugin. Needed for all clifs plugins.
        """
        time_start = time.time()

        for dir_pair in self.dir_pairs:
            self.backup_dir(dir_pair.source, dir_pair.dest)
        time_end = time.time()
        time_run = (time_end - time_start) / 60
        self.console.print(
            f"Hurray! All files backed up in only {time_run:5.2f} minutes"
        )

    def get_backup_tasks(
        self, progress: Dict[str, Progress], files_total: int
    ) -> Dict[str, TaskID]:
        return {
            "progress_backup": progress["overall"].add_task(
                "Storing data:  ", total=files_total, last_action="-"
            ),
            "count_files_found": progress["counts"].add_task(
                "Files processed:", total=None
            ),
            "count_files_added": progress["counts"].add_task(
                "Files added:", total=None
            ),
            "count_files_updated": progress["counts"].add_task(
                "Files updated:", total=None
            ),
            "count_files_untouched": progress["counts"].add_task(
                "Files untouched:", total=None
            ),
        }

    def get_delete_tasks(
        self, progress: Dict[str, Progress], files_total: int, dirs_total: int
    ) -> Dict[str, TaskID]:
        return {
            "progress_delete_files": progress["overall"].add_task(
                "Deleting files:",
                total=files_total,
                last_action="-",
                last_action_desc="Last file deleted",
            ),
            "progress_delete_folders": progress["overall"].add_task(
                "Deleting dirs:",
                total=dirs_total,
                last_action="-",
                last_action_desc="Last dir deleted",
            ),
            "count_files_found": progress["counts"].add_task(
                "Files processed:", total=None
            ),
            "count_files_deleted": progress["counts"].add_task(
                "Files deleted:", total=None
            ),
            "count_folders_found": progress["counts"].add_task(
                "Dirs processed:", total=None
            ),
            "count_folders_deleted": progress["counts"].add_task(
                "Dirs deleted:", total=None
            ),
        }

    def backup_dir(
        self,
        dir_source: Path,
        dir_dest: Path,
    ) -> None:
        print_line(console=self.console)
        self.console.print(f"Backing up files \nfrom: {dir_source}\nto:   {dir_dest}")

        if not dir_source.is_dir():
            self.console.print(
                set_style(
                    f"Warning: the source directory does not exist. "
                    f"Nothing to back up from:\n{dir_source}",
                    "warning",
                )
            )
            return

        files_source, dirs_source = list_filedirs(dir_source)
        self.copy_data(
            dir_source=dir_source,
            dir_dest=dir_dest,
            files_source=files_source,
        )

        if self.delete:
            self.console.print("All files stored, checking for files to delete now.")

            self.delete_obsolete_data(
                dir_source=dir_source,
                dir_dest=dir_dest,
                files_source=files_source,
                dirs_source=dirs_source,
            )
        print_line(console=self.console)

    def copy_data(
        self, dir_source: Path, dir_dest: Path, files_source: List[Path]
    ) -> None:
        progress: Dict[str, Progress] = {
            "counts": get_count_progress(),
            "overall": get_last_action_progress(),
        }

        tasks = self.get_backup_tasks(progress, len(files_source))

        progress_table = Table.grid()
        progress_table.add_row(
            Panel.fit(
                progress["overall"],
                title="Progress Backup",
                border_style="cyan",
                padding=(2, 2),
            ),
            Panel.fit(
                progress["counts"],
                title="Counts",
                border_style="bright_black",
                padding=(1, 2),
            ),
        )

        with Live(
            progress_table,
            console=self.console,
            auto_refresh=False,
        ) as live:
            for cur_file in files_source:
                progress["counts"].advance(tasks["count_files_found"])
                action = conditional_copy(
                    cur_file,
                    Path(str(cur_file).replace(str(dir_source), str(dir_dest))),
                    dry_run=self.dry_run,
                )
                if action:
                    progress["overall"].update(
                        tasks["progress_backup"],
                        last_action=f"{action} {cur_file.name}",
                    )
                    if action == "adding":
                        progress["counts"].advance(tasks["count_files_added"])
                    elif action == "updating":
                        progress["counts"].advance(tasks["count_files_updated"])
                    if self.verbose:
                        live.console.print(f"  - {action} [cyan]'{cur_file.name}'[/]")
                else:
                    progress["counts"].advance(tasks["count_files_untouched"])
                progress["overall"].advance(tasks["progress_backup"])
                live.refresh()

    def delete_obsolete_data(
        self,
        dir_source: Path,
        dir_dest: Path,
        files_source: List[Path],
        dirs_source: List[Path],
    ) -> None:
        files_dest, dirs_dest = list_filedirs(dir_dest)

        progress: Dict[str, Progress] = {
            "counts": get_count_progress(),
            "overall": get_last_action_progress(),
        }
        tasks_delete = self.get_delete_tasks(progress, len(files_dest), len(dirs_dest))

        progress_table = Table.grid()
        progress_table.add_row(
            Panel.fit(
                progress["overall"],
                title="Progress Deletion",
                border_style="magenta",
                padding=(1, 2),
            ),
            Panel.fit(
                progress["counts"],
                title="Counts",
                border_style="bright_black",
                padding=(1, 2),
            ),
        )

        with Live(
            progress_table,
            console=self.console,
            auto_refresh=False,
        ) as live:
            for cur_file_dest in files_dest:
                progress["counts"].advance(tasks_delete["count_files_found"])
                action = conditional_delete(
                    Path(str(cur_file_dest).replace(str(dir_dest), str(dir_source))),
                    cur_file_dest,
                    files_source,
                    dry_run=self.dry_run,
                )
                if action:
                    progress["counts"].advance(tasks_delete["count_files_deleted"])
                    progress["overall"].update(
                        tasks_delete["progress_delete_files"],
                        last_action=cur_file_dest.name,
                    )
                    if self.verbose:
                        live.console.print(
                            f"  - deleting [magenta]'{cur_file_dest.name}'[/] "
                            "from dest dir"
                        )

                progress["overall"].advance(tasks_delete["progress_delete_files"])
                live.refresh()

            for cur_dir_dest in dirs_dest:
                progress["counts"].advance(tasks_delete["count_folders_found"])
                action = conditional_delete(
                    Path(str(cur_dir_dest).replace(str(dir_dest), str(dir_source))),
                    cur_dir_dest,
                    dirs_source,
                    dry_run=self.dry_run,
                )
                if action:
                    progress["counts"].advance(tasks_delete["count_folders_deleted"])
                    progress["overall"].update(
                        tasks_delete["progress_delete_folders"],
                        last_action=cur_dir_dest.name,
                    )
                    if self.verbose:
                        live.console.print(
                            f"  - deleting dir [magenta]'{cur_dir_dest.name}'[/] "
                            "from dest dir"
                        )
                progress["overall"].advance(tasks_delete["progress_delete_folders"])
                live.refresh()
