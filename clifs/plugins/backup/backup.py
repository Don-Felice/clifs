# -*- coding: utf-8 -*-

import csv
import shutil
import time
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from pathlib import Path
from typing import List, Optional, Tuple

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_cli import cli_bar

DirPair = namedtuple("DirPair", ["source", "dest"])


def conditional_copy(path_source: Path, path_dest: Path, dry_run: bool = False) -> int:
    """
    Copy only if dest file does not exist or is older than the souce file.
    """
    process = None
    if not path_dest.exists():
        process = "copying"
    elif (path_source.stat().st_mtime - path_dest.stat().st_mtime) > 1:
        process = "updating from"

    if process is not None:
        print(f" - {process} {str(path_source)}", flush=True)
        if not dry_run:
            path_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path_source, path_dest)
        return 1
    return 0


def conditional_delete(
    path_source: Path, path_dest: Path, list_source: List[Path], dry_run: bool = False
) -> int:
    """
    Delete only if `path_source`is not in `list_source`.
    """
    if path_source not in list_source:
        if path_dest.is_dir():
            print(f" - deleting dir {str(path_dest)}", flush=True)
            if not dry_run:
                shutil.rmtree(str(path_dest))
        else:
            filename = path_dest.name
            print(f" - deleting {filename}", flush=True)
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

    dir_source: Path
    dir_dest: Path
    config_file: Path
    delete: bool
    dry_run: bool

    @staticmethod
    def init_parser(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs plugins.
        """

        parser.add_argument(
            "-s", "--dir_source", type=Path, default=None, help="source directory"
        )
        parser.add_argument(
            "-d", "--dir_dest", type=Path, default=None, help="destination directory"
        )
        parser.add_argument(
            "-cfg",
            "--cfg_file",
            type=Path,
            default=None,
            help="path to the config file",
        )
        parser.add_argument(
            "-del",
            "--delete",
            action="store_true",
            default=False,
            help=(
                "delete files which exist in destination directory but not in"
                "the source directory"
            ),
        )
        parser.add_argument(
            "-dr",
            "--dry_run",
            action="store_true",
            default=False,
            help="Do not touch anything",
        )

    def __init__(self, args: Namespace) -> None:
        self.dir_source: Optional[Path] = args.dir_source
        self.dir_dest: Optional[Path] = args.dir_dest
        self.cfg_file: Optional[Path] = args.cfg_file
        self.delete: bool = args.delete
        self.dry_run: bool = args.dry_run

        assert not (
            self.cfg_file and self.dir_source or self.cfg_file and self.dir_dest
        ), (
            "Paths provided in config table and as parameters. "
            "You'll have to decide for one option I am afraid."
        )

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

        else:
            self.dir_pairs = [DirPair(self.dir_source, self.dir_dest)]

    def run(self) -> None:
        """
        Running the plugin. Needed for all clifs plugins.
        """
        time_start = time.time()

        for dir_pair in self.dir_pairs:
            print(f"Backing up files in {dir_pair.source} in {dir_pair.dest}.")
            self.backup_dir(
                dir_pair.source, dir_pair.dest, delete=self.delete, dry_run=self.dry_run
            )
        time_end = time.time()
        time_run = (time_end - time_start) / 60
        print(f"Hurray! All files backed up in only {time_run:5.2f} minutes")

    @staticmethod
    def backup_dir(
        dir_source: Path,
        dir_dest: Path,
        delete: bool = False,
        dry_run: bool = False,
    ) -> None:
        print(f"Backing up files in {dir_source} to {dir_dest}.")

        list_files_source, list_dirs_source = list_filedirs(dir_source)
        # initialize stats
        counter = {"checked": len(list_files_source), "copied": 0, "deleted": 0}

        for cur_num_file, cur_file in enumerate(list_files_source, start=1):
            counter["copied"] += conditional_copy(
                cur_file,
                Path(str(cur_file).replace(str(dir_source), str(dir_dest))),
                dry_run=dry_run,
            )
            cli_bar(cur_num_file, counter["checked"], suffix="of files checked")

        if delete:
            print("All files stored, checking for files to delete now.")
            list_files_dest, list_dirs_dest = list_filedirs(dir_dest)

            num_dest = len(list_files_dest)
            for cur_num_file, cur_file_dest in enumerate(list_files_dest, start=1):
                counter["deleted"] += conditional_delete(
                    Path(str(cur_file_dest).replace(str(dir_dest), str(dir_source))),
                    cur_file_dest,
                    list_files_source,
                    dry_run=dry_run,
                )
                cli_bar(cur_num_file, num_dest, suffix="of files checked")

            for cur_dir_dest in list_dirs_dest:
                conditional_delete(
                    Path(str(cur_dir_dest).replace(str(dir_dest), str(dir_source))),
                    cur_dir_dest,
                    list_dirs_source,
                    dry_run=dry_run,
                )

        print(
            f"\nStored {counter['copied']} files out of {counter['checked']} from "
            f"'{dir_source}'.\n"
            f"Deleted {counter['deleted']} files in destination directory."
        )
