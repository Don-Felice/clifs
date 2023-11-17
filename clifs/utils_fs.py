"""
Utilities for the file system
"""

import csv
import re
import shutil
import sys
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
from typing import List, Optional, Set

from clifs.utils_cli import AnsiColor, cli_bar, print_line, wrap_string

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

    def get_files2process(self) -> List[Path]:
        files2process = self._get_files_by_filterstring(
            self.dir_source, filterstring=self.filterstring, recursive=self.recursive
        )

        if self.filterlist:
            list_filter = _list_from_csv(
                self.filterlist, self.filterlistheader, self.filterlistsep
            )
            files2process = self._filter_by_list(files2process, list_filter)
        return files2process

    @staticmethod
    def exit_if_nothing_to_process(files2process: list) -> None:
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


def _find_bad_char(string: str) -> List[str]:
    """Check stings for characters causing problems in windows file system."""
    bad_chars = r"~“#%&*:<>?/\{|}"
    return [x for x in bad_chars if x in string]


def _get_path_dest(
    path_src: Path, path_file: Path, path_out: Path, flatten: bool = False
) -> Path:
    if flatten:
        return path_out / path_file.name
    return Path(str(path_file).replace(str(path_src), str(path_out)))


def _list_from_csv(
    path_csv: Path, header: Optional[str] = None, delimiter: str = ","
) -> List[str]:
    if not header:
        res_list = path_csv.open().read().splitlines()
    else:
        with path_csv.open(newline="") as infile:
            reader = csv.DictReader(infile, delimiter=delimiter)
            res_list = []
            for row in reader:
                try:
                    res_list.append(row[header])
                except KeyError:
                    print(
                        f"Provided csv does not contain header '{header}'. "
                        f"Found headers: {list(row.keys())}"
                    )
                    raise
    return res_list


def _get_unique_path(
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


def _print_rename_message(
    message: str,
    num_file: int,
    num_files_all: int,
    preview_mode: bool = False,
    space_prefix: str = "    ",
) -> None:
    if preview_mode:
        print(space_prefix + message)
    else:
        cli_bar(num_file, num_files_all, suffix=space_prefix + message)


def como(  # pylint: disable=too-many-arguments
    dir_source: Path,
    dir_dest: Path,
    *,
    files2process: List[Path],
    move: bool = False,
    skip_existing: bool = False,
    keep_all: bool = False,
    flatten: bool = False,
    dry_run: bool = False,
) -> None:
    assert not (skip_existing and keep_all), (
        "You can only choose to either skip existing files "
        "or keep both versions. Choose wisely!"
    )

    dir_dest.parent.mkdir(exist_ok=True, parents=True)

    str_process = "moving" if move else "copying"
    print(
        f"{str_process} {len(files2process)} files from:"
        f"\n{dir_source}"
        f"\nto"
        f"\n{dir_dest}"
    )
    print_line()

    num_file = 0
    num_files2process = len(files2process)
    for num_file, file in enumerate(files2process, 1):
        txt_report = f"Last: {file.name}"
        filepath_dest = _get_path_dest(dir_source, file, dir_dest, flatten=flatten)
        if skip_existing:
            if filepath_dest.exists():
                txt_report = wrap_string(
                    f"Skipped as already present: " f"{file.name}",
                    AnsiColor.YELLOW,
                )
                cli_bar(
                    num_file,
                    num_files2process,
                    suffix="of files processed. " + txt_report,
                )
                continue
        elif keep_all:
            filepath_dest_new = _get_unique_path(filepath_dest)
            if filepath_dest_new != filepath_dest:
                txt_report = wrap_string(
                    f"Changed name as already present: "
                    f"{filepath_dest.name} -> {filepath_dest_new.name}",
                    AnsiColor.YELLOW,
                )
                filepath_dest = filepath_dest_new
        else:
            if filepath_dest.exists():
                txt_report = wrap_string(
                    f"Replacing existing version for: {file.name}",
                    AnsiColor.YELLOW,
                )

        if not dry_run:
            if not flatten:
                filepath_dest.parent.mkdir(exist_ok=True, parents=True)
            if move:
                shutil.move(str(file), str(filepath_dest))
            else:
                shutil.copy2(str(file), str(filepath_dest))
        cli_bar(
            num_file,
            num_files2process,
            suffix="of files processed. " + txt_report,
        )
    print_line()
    str_process = "moved" if move else "copied"
    print(f"Hurray, {num_file} files have been {str_process}.")


def rename_files(
    files2process: List[Path],
    pattern: str,
    replacement: str,
    *,
    preview_mode: bool = True,
) -> None:
    counter = Counter(files2process=len(files2process))
    print(f"Renaming {counter['files2process']} files.")
    print_line()
    files_to_be_added: Set[Path] = set()
    files_to_be_deleted: Set[Path] = set()
    if preview_mode:
        print("Preview:")

    num_file = 0
    for num_file, path_file in enumerate(files2process, 1):
        name_old = path_file.name
        name_new = re.sub(pattern, replacement, name_old)
        message_rename = f"{name_old:35} -> {name_new:35}"

        # skip files if renaming would result in bad characters
        found_bad_chars = _find_bad_char(name_new)
        if found_bad_chars:
            message_rename += wrap_string(
                f"{INDENT}Warning: not doing renaming as it would result "
                f"in bad characters: {','.join(found_bad_chars)}"
            )
            counter["bad_results"] += 1
            _print_rename_message(
                message_rename,
                num_file,
                counter["files2process"],
                preview_mode=preview_mode,
            )
            continue

        # make sure resulting paths are unique
        path_file_new = path_file.parent / name_new
        path_file_unique = _get_unique_path(
            path_file_new,
            set_taken=files_to_be_added,
            set_free=files_to_be_deleted | {path_file},
        )

        if path_file_new != path_file_unique:
            path_file_new = path_file_unique
            name_new = path_file_unique.name
            message_rename = f"{name_old:35} -> {name_new:35}"
            message_rename += wrap_string(
                f"{INDENT}Warning: name result would already exist. "
                "Adding number suffix.",
                AnsiColor.YELLOW,
            )
            counter["name_conflicts"] += 1

        # skip files that are not renamed
        if path_file_new == path_file:
            message_rename = wrap_string(message_rename, AnsiColor.GRAY)
            _print_rename_message(
                message_rename,
                num_file,
                counter["files2process"],
                preview_mode=preview_mode,
            )
            continue

        _print_rename_message(
            message_rename,
            num_file,
            counter["files2process"],
            preview_mode=preview_mode,
        )
        if not preview_mode:
            path_file.rename(path_file_new)
            counter["files_renamed"] += 1
        else:
            files_to_be_added.add(path_file_new)
            if path_file_new in files_to_be_deleted:
                files_to_be_deleted.remove(path_file_new)
            files_to_be_deleted.add(path_file)

    if counter["bad_results"] > 0:
        print(
            wrap_string(
                f"Warning: {counter['bad_results']} out of {counter['files2process']} "
                f"files not renamed as it would result in bad characters.",
            )
        )

    if counter["name_conflicts"] > 0:
        print(
            wrap_string(
                f"Warning: {counter['name_conflicts']} out of "
                f"{counter['files2process']} renamings would have resulted in name "
                "conflicts. Added numbering suffices to get unique names.",
                AnsiColor.YELLOW,
            )
        )

    print_line()
    if not preview_mode:
        print(
            f"Hurray, {num_file} files have been processed, "
            f"{counter['files_renamed']} have been renamed.",
            AnsiColor.YELLOW,
        )


def delete_files(files2process: List[Path], dry_run: bool = False):
    num_files2process = len(files2process)
    print(f"Deleting {num_files2process} files.")
    print_line()

    num_file = 0
    for num_file, path_file in enumerate(files2process, 1):
        if dry_run:
            print(f"would delete: {path_file.name}")
        else:
            path_file.unlink(missing_ok=True)
            cli_bar(
                num_file,
                num_files2process,
                suffix=f"of files deleted. Last: {path_file.name}",
            )
    print_line()
    if not dry_run:
        print(f"Hurray, {num_file} files have been deleted.")
