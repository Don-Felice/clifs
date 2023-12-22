"""Utilities for the file system"""

import csv
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple

INDENT = "    "


class PathGetterMixin:
    """
    Get paths from a source directory by different filter methods.
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

    def get_paths(self) -> Tuple[List[Path], List[Path]]:
        """Get file and folder paths depending on set filters

        :return: Lists of file paths and folder paths matching the filters respectively
        """
        files, dirs = self._get_paths_by_filterstring(
            self.dir_source, filterstring=self.filterstring, recursive=self.recursive
        )

        if self.filterlist:
            list_filter = self._list_from_csv()
            files = [i for i in files if i.name in list_filter]
            dirs = [i for i in dirs if i.name in list_filter]
        return files, dirs

    @staticmethod
    def exit_if_nothing_to_process(items: List[Any]) -> None:
        """Exit running process if list of files to process is empty"""
        if not items:
            print("Nothing to process.")
            sys.exit(0)

    @staticmethod
    def sort_paths(paths: List[Path]) -> List[Path]:
        """Sort by inverse depth and str

        :param paths: List of paths to sort
        :return: Sorted list of paths
        """
        return sorted(paths, key=lambda x: (-len(x.parents), str(x)))

    @staticmethod
    def _get_paths_by_filterstring(
        dir_source: Path, filterstring: Optional[str] = None, recursive: bool = False
    ) -> Tuple[List[Path], List[Path]]:
        """Get files by substring filter on the file name.

        :param dir_source: directory to search for files in
        :param filterstring: Substring that must be included in a file name.
            If set to None, files are not filtered by substring. Defaults to None.
        :param recursive: Search recursively, defaults to False
        :return: Lists of file paths and dir paths matching the filter respectively
        """
        pattern_search = f"*{filterstring}*" if filterstring else "*"
        if recursive:
            pattern_search = "**/" + pattern_search
        files = []
        dirs = []
        for path in dir_source.glob(pattern_search):
            if path.is_dir():
                dirs.append(path.resolve())
            else:
                files.append(path.resolve())

        return files, dirs

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
    """Given a name candidate get a unique file name in a given directory.

    Adds number suffixes in form ' (#)' if file name is already taken.

    :param path_candidate: Candidate for a file path.
    :param set_taken: Optional set of additional paths which are considered as already
        taken, defaults to None
    :param set_free: Optional sets of paths that are considered as not taken even if
        corresponding files exist, defaults to None
    :raises ValueError: If there are common elements in 'set_taken' and 'set_free'
    :return: Unique file path
    """
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
