"""
Utilities for the file system
"""

import csv
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, List, Optional, Set

INDENT = "    "


class FileGetterMixin:
    """
    Get files from a source directory by different filter methods.
    """

    dir_source: Path
    recursive: bool
    filterlist: Path
    filterlistheader: str
    filterlistsep: str
    filterstring: str

    @staticmethod
    def init_parser_mixin(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        parser.add_argument(
            "dir_source",
            type=Path,
            help="Folder with files to copy/move from",
        )
        parser.add_argument(
            "-r",
            "--recursive",
            action="store_true",
            help="Search recursively in source folder",
        )
        parser.add_argument(
            "-fl",
            "--filterlist",
            default=None,
            type=Path,
            help="Path to a txt or csv file containing a list of files to process. "
            "In case of a CSV, separator and header can be provided additionally via "
            "the parameters `filterlistsep` and `filterlistheader`. "
            "If no header is provided, each line in the file is treated as individual "
            "file name.",
        )
        parser.add_argument(
            "-flh",
            "--filterlistheader",
            default=None,
            help="Header of the column to use as filter "
            "from a csv provided as filterlist."
            " If no header is provided, "
            "each line in the file is read as individual item name.",
        )
        parser.add_argument(
            "-fls",
            "--filterlistsep",
            default=",",
            help="Separator to use for csv provided as filter list. Default: ','",
        )
        parser.add_argument(
            "-fs",
            "--filterstring",
            default=None,
            help="Substring identifying files to be copied. not case sensitive.",
        )

    def get_files(self) -> List[Path]:
        files2process = self._get_files_by_filterstring(
            self.dir_source, filterstring=self.filterstring, recursive=self.recursive
        )

        if self.filterlist:
            list_filter = self._list_from_csv()
            files2process = self._filter_by_list(files2process, list_filter)
        return files2process

    @staticmethod
    def exit_if_nothing_to_process(files2process: List[Any]) -> None:
        if not files2process:
            print("Nothing to process.")
            sys.exit(0)

    @staticmethod
    def _get_files_by_filterstring(
        dir_source: Path, filterstring: Optional[str] = None, recursive: bool = False
    ) -> List[Path]:
        pattern_search = f"*{filterstring}*" if filterstring else "*"
        if recursive:
            pattern_search = "**/" + pattern_search
        return [file for file in dir_source.glob(pattern_search) if not file.is_dir()]

    @staticmethod
    def _filter_by_list(files: List[Path], list_filter: List[str]) -> List[Path]:
        return [i for i in files if i.name in list_filter]

    def _list_from_csv(self) -> List[str]:
        if not self.filterlistheader:
            res_list = self.filterlist.open().read().splitlines()
        else:
            with self.filterlist.open(newline="") as infile:
                reader = csv.DictReader(infile, delimiter=self.filterlistsep)
                res_list = []
                for row in reader:
                    try:
                        res_list.append(row[self.filterlistheader])
                    except KeyError:
                        print(
                            "Provided csv does not contain header "
                            f"'{self.filterlistheader}'. Found headers:\n"
                            f"{list(row.keys())}"
                        )
                        raise
        return res_list


def get_unique_path(
    path_candidate: Path,
    set_taken: Optional[Set[Path]] = None,
    set_free: Optional[Set[Path]] = None,
) -> Path:
    if set_taken is None:
        set_taken = set()
    if set_free is None:
        set_free = set()
    if intersect := set_taken.intersection(set_free):
        raise ValueError(
            "Params 'set_taken' and 'set_free' contain common elements: \n"
            f"{intersect=}."
        )

    path_new = path_candidate
    if (path_new.exists() or path_new in set_taken) and (path_new not in set_free):
        name_file = path_new.stem
        count_match = re.match(r".* \((\d+)\)$", name_file)
        if count_match:
            count = int(count_match.group(1)) + 1
            name_file = " ".join(name_file.split(" ")[0:-1])
        else:
            count = 2

        while (path_new.exists() or path_new in set_taken) and (
            path_new not in set_free
        ):
            name_file_new = name_file + f" ({count})"
            path_new = path_candidate.parent / (name_file_new + path_candidate.suffix)
            count += 1
    return path_new
