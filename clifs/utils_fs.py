# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import csv
from pathlib import Path
import re
import shutil
import sys
from typing import List, Set, Union, Optional


from clifs.utils_cli import wrap_string, cli_bar, ANSI_COLORS, print_line


class FileGetterMixin:
    """
    Get files from a source directory by different filter methods.
    """

    dir_source: Union[str, Path]
    recursive: bool
    filterlist: Path
    filterlistheader: str
    filterlistsep: str
    filterstring: str

    @staticmethod
    def init_parser_mixin(parser: ArgumentParser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        parser.add_argument(
            "dir_source", type=Path, help="Folder with files to copy/move from"
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
            help="Path to a txt or csv file containing a list of files to copy/move."
            "In case of a CSV, separator and header can be provided additionally. "
            "If no header is provided, "
            "each line in the file is read as individual item name.",
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

    def get_files2process(
        self,
        dir_source: Path,
        recursive: bool = False,
        path_filterlist: Optional[Path] = None,
        header_filterlist: Optional[str] = None,
        sep_filterlist: str = ",",
        filterstring: Optional[str] = None,
    ) -> List[Path]:
        files2process = self._get_files_by_filterstring(
            dir_source, filterstring=filterstring, recursive=recursive
        )

        if path_filterlist:
            list_filter = _list_from_csv(
                path_filterlist, header_filterlist, sep_filterlist
            )
            files2process = self._filter_by_list(files2process, list_filter)
        return files2process

    @staticmethod
    def exit_if_nothing_to_process(files2process: list):
        if not files2process:
            print("Nothing to process.")
            sys.exit(0)

    @staticmethod
    def _get_files_by_filterstring(
        dir_source: Path, filterstring: Optional[str] = None, recursive: bool = False
    ) -> List[Path]:
        pattern_search = "*" + filterstring + "*" if filterstring else "*"
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
    else:
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
    to_avoid_additionally: Set[Path] = None,
    to_allow_additionally: Set[Path] = None,
) -> Path:
    if to_avoid_additionally is None:
        to_avoid_additionally = set()
    if to_allow_additionally is None:
        to_allow_additionally = set()

    if to_avoid_additionally.intersection(to_allow_additionally):
        raise ValueError(
            "Params 'to_avoid_addiotionally' and 'to_allow_additionally' contain "
            "common elements: "
            f"{to_avoid_additionally.intersection(to_allow_additionally)}."
        )
    name_file = path_candidate.stem

    if (path_candidate not in to_allow_additionally) and (
        path_candidate.exists() or path_candidate in to_avoid_additionally
    ):
        count_match = re.match(r".* \((\d+)\)$", name_file)
        if count_match:
            count = int(count_match.group(1)) + 1
            name_file_new = " ".join(name_file.split(" ")[0:-1]) + f" ({count})"
        else:
            name_file_new = name_file + " (2)"
        path_new = path_candidate.parent / (name_file_new + path_candidate.suffix)
        return _get_unique_path(path_new, to_avoid_additionally, to_allow_additionally)
    else:
        return path_candidate


def _print_rename_message(
    message: str,
    num_file: int,
    num_files_all: int,
    preview_mode: bool = False,
    space_prefix: str = "    ",
):
    if preview_mode:
        print(space_prefix + message)
    else:
        cli_bar(num_file, num_files_all, suffix=space_prefix + message)


def como(
    dir_source: Path,
    dir_dest: Path,
    *,
    files2process: List[Path],
    move: bool = False,
    skip_existing: bool = False,
    keep_all: bool = False,
    flatten: bool = False,
    dry_run: bool = False,
):
    assert not (skip_existing and keep_all), (
        "You can only choose to either skip existing files "
        "or keep both versions. Choose wisely!"
    )

    dir_source = Path(dir_source)
    dir_dest = Path(dir_dest)

    dir_dest.parent.mkdir(exist_ok=True, parents=True)

    str_process = "moving" if move else "copying"
    print(
        f"Will start {str_process} {len(files2process)} files from:"
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
                    ANSI_COLORS["yellow"],
                )
                cli_bar(
                    num_file,
                    num_files2process,
                    suffix="of files processed. " + txt_report,
                )
                continue
        elif keep_all:
            filepath_dest_new = _get_unique_path(filepath_dest)
            if not filepath_dest_new == filepath_dest:
                txt_report = wrap_string(
                    f"Changed name as already present: "
                    f"{filepath_dest.name} -> {filepath_dest_new.name}",
                    ANSI_COLORS["yellow"],
                )
                filepath_dest = filepath_dest_new
        else:
            if filepath_dest.exists():
                txt_report = wrap_string(
                    f"Replacing existing version for: " f"{file.name}",
                    ANSI_COLORS["yellow"],
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
    re_pattern: str,
    replacement: str,
    *,
    preview_mode: bool = True,
):
    num_files2process = len(files2process)
    print(f"Renaming {num_files2process} files.")
    print_line()
    files_to_be_added: Set[Path] = set()
    files_to_be_deleted: Set[Path] = set()
    if preview_mode:
        print("Preview:")

    num_bad_results = 0
    num_name_conflicts = 0
    num_files_renamed = 0
    num_file = 0
    for num_file, path_file in enumerate(files2process, 1):
        name_old = path_file.name
        name_new = re.sub(re_pattern, replacement, name_old)
        message_rename = f"{name_old:35} -> {name_new:35}"

        # skip files if renaming would result in bad characters
        found_bad_chars = _find_bad_char(name_new)
        if found_bad_chars:
            str_bad_chars = ",".join(found_bad_chars)
            message_rename += wrap_string(
                "    Warning: not doing renaming as it would result "
                f'in bad characters "{str_bad_chars}" '
            )
            num_bad_results += 1
            _print_rename_message(
                message_rename, num_file, num_files2process, preview_mode=preview_mode
            )
            continue

        # make sure resulting paths are unique
        path_file_new = path_file.parent / name_new
        path_file_unique = _get_unique_path(
            path_file_new,
            to_avoid_additionally=files_to_be_added,
            to_allow_additionally=files_to_be_deleted | {path_file},
        )

        if not path_file_new == path_file_unique:
            path_file_new = path_file_unique
            name_new = path_file_unique.name
            message_rename = f"{name_old:35} -> {name_new:35}"
            message_rename += wrap_string(
                "    Warning: resulting name would already be present in folder. "
                "Will add numbering suffix.",
                ANSI_COLORS["yellow"],
            )
            num_name_conflicts += 1

        # skip files that are not renamed
        if path_file_new == path_file:
            message_rename = wrap_string(message_rename, ANSI_COLORS["gray"])
            _print_rename_message(
                message_rename, num_file, num_files2process, preview_mode=preview_mode
            )
            continue

        _print_rename_message(
            message_rename, num_file, num_files2process, preview_mode=preview_mode
        )
        if not preview_mode:
            path_file.rename(path_file_new)
            num_files_renamed += 1
        else:
            files_to_be_added.add(path_file_new)
            if path_file_new in files_to_be_deleted:
                files_to_be_deleted.remove(path_file_new)
            files_to_be_deleted.add(path_file)

    if num_bad_results:
        print(
            wrap_string(
                f"Warning: {num_bad_results} out of {num_files2process} "
                f"files not renamed as it would result in bad characters."
            )
        )
    if num_name_conflicts:
        print(
            wrap_string(
                f"Warning: {num_name_conflicts} out of {num_files2process} "
                f"renamings would have resulted in name conflicts. "
                f"Added numbering suffices to get unique names."
            )
        )
    print_line()
    if not preview_mode:
        print(
            f"Hurray, {num_file} files have been processed, "
            f"{num_files_renamed} have been renamed."
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
