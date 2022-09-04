# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace


from collections import namedtuple
import csv
from pathlib import Path
import shutil
from typing import Optional, Union, List
import time

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_cli import cli_bar

DirPair = namedtuple("DirPair", ["source", "dest"])


def conditional_copy(path_source: Path, path_dest: Path, dry_run: bool = False):
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
    else:
        return 0


def conditional_delete(
    path_source: Path, path_dest: Path, list_source: List[Path], dry_run: bool = False
):
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
    else:
        return 0


def list_filedirs(dir_source: Union[str, Path]):
    """
    List files and directories in a source dir.
    """
    if isinstance(dir_source, str):
        dir_source = Path(dir_source)

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

    @staticmethod
    def init_parser(parser: ArgumentParser):
        """
        Adding arguments to an argparse parser. Needed for all clifs plugins.
        """

        parser.add_argument(
            "-s", "--dir_source", type=str, default=None, help="source directory"
        )
        parser.add_argument(
            "-d", "--dir_dest", type=str, default=None, help="destination directory"
        )
        parser.add_argument(
            "-cfg", "--cfg_file", type=str, default=None, help="destination directory"
        )
        parser.add_argument(
            "-del",
            "--delete",
            action="store_true",
            default=False,
            help="delete files which exist in destination directory but not in the source directory",
        )
        parser.add_argument(
            "-dr",
            "--dry_run",
            action="store_true",
            default=False,
            help="destination directory",
        )

    def __init__(self, args: Namespace):

        self.dir_source: Optional[Union[str, Path]] = args.dir_source
        self.dir_dest: Optional[Union[str, Path]] = args.dir_dest
        self.cfg_file: Optional[Union[str, Path]] = args.cfg_file
        self.delete: bool = args.delete
        self.dry_run: bool = args.dry_run

        assert not (
            self.cfg_file and self.dir_source or self.cfg_file and self.dir_dest
        ), (
            "Paths provided in config table and as parameters. "
            "You'll have to decide for one option I am afraid."
        )

        if self.cfg_file:
            # TODO: check_cfg_format(cfg_file)
            self.dir_pairs = []
            with open(self.cfg_file, newline="\n") as cfg_file:
                reader = csv.DictReader(cfg_file, fieldnames=["source_dir", "dest_dir"])
                # skip header row
                next(reader)
                for row in reader:
                    self.dir_pairs.append(DirPair(row["source_dir"], row["dest_dir"]))

        else:
            self.dir_pairs = [DirPair(self.dir_source, self.dir_dest)]

    def run(self):
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
        dir_source: Union[str, Path],
        dir_dest: Union[str, Path],
        delete: bool = False,
        dry_run: bool = False,
    ):
        """

        :param delete:
        :param dir_source:
        :param dir_dest:
        :param dry_run:
        :return:
        """
        if isinstance(dir_source, str):
            dir_source = Path(dir_source)
        if isinstance(dir_dest, str):
            dir_dest = Path(dir_dest)

        print(f"Backing up files in {dir_source} to {dir_dest}.")

        list_files_source, list_dirs_source = list_filedirs(dir_source)
        # initialize stats
        num_checked = len(list_files_source)
        num_copied = 0
        num_deleted = 0

        for cur_num_file, cur_file in enumerate(list_files_source, start=1):
            cur_dest = Path(str(cur_file).replace(str(dir_source), str(dir_dest)))
            num_copied += conditional_copy(cur_file, cur_dest, dry_run=dry_run)
            cli_bar(cur_num_file, num_checked, suffix="of files checked")
            cur_num_file += 1

        if delete:
            print("All files stored, checking for files to delete now.")
            list_files_dest, list_dirs_dest = list_filedirs(dir_dest)

            num_dest = len(list_files_dest)
            for cur_num_file, cur_file_dest in enumerate(list_files_dest, start=1):
                cur_file_source = Path(
                    str(cur_file_dest).replace(str(dir_dest), str(dir_source))
                )
                num_deleted += conditional_delete(
                    cur_file_source, cur_file_dest, list_files_source, dry_run=dry_run
                )
                cli_bar(cur_num_file, num_dest, suffix="of files checked")
                cur_num_file += 1

            for cur_dir_dest in list_dirs_dest:
                cur_dir_source = Path(
                    str(cur_dir_dest).replace(str(dir_dest), str(dir_source))
                )
                conditional_delete(
                    cur_dir_source, cur_dir_dest, list_dirs_source, dry_run=dry_run
                )

        print(
            f'\nStored {num_copied} files out of {num_checked} from "{dir_source}".'
            f"\nDeleted {num_deleted} files in destination directory."
        )
