"""Common utils for testing"""

import os
import re
from pathlib import Path

import pytest


def get_files(dir, sub_str=None):
    pattern = "*" if sub_str is None else f"*{sub_str}*"
    return [path for path in dir.rglob(pattern) if path.is_file()]


def update_mtime(path_file):
    with path_file.open("a") as filetoupdate:
        filetoupdate.write("I have been updated.")


def escape_ansi(string):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", string)


def escape_rich_style(string):
    style_escape = re.compile(r"(?<!\\)\[[^\]]*[^\\]\]")
    return style_escape.sub("", string)


def check_mtime_consistency(file1, file2):
    assert (
        abs(os.path.getmtime(file1) - os.path.getmtime(file2)) <= 1
    ), f"File modification time is not consistent for file {file1}"


def assert_files_present(dir_source, dir_ref, check_mtime=True):
    print("---------------------")
    print(
        f"checking consistencies of folders:"
        f"\n{str(dir_source)}\nand\n{str(dir_ref)}."
    )
    list_files_source = [x for x in dir_source.rglob("*") if not x.is_dir()]
    for cur_file_source in list_files_source:
        cur_file_dest = Path(
            str(cur_file_source).replace(str(dir_source), str(dir_ref))
        )
        print(f"checking file: {cur_file_source}")
        # check for existence
        assert (
            cur_file_dest.exists()
        ), f"file {cur_file_source.name} from {dir_source} not existent in {dir_ref}."
        if check_mtime:
            # check for proper updating
            check_mtime_consistency(cur_file_source, cur_file_dest)
    print("---------------------")


def substr_in_dir_names(directory, sub_str="DELME", files_only=False, dirs_only=False):
    if files_only:
        return any([sub_str in x.name for x in directory.rglob("*") if x.is_file()])
    elif dirs_only:
        return any([sub_str in x.name for x in directory.rglob("*") if x.is_dir()])
    else:
        return any([sub_str in x.name for x in directory.rglob("*")])


def parametrize_default_ids(argname, argvalues, indirect=False, ids=None, scope=None):
    if not ids:
        argnames = argname.split(",") if isinstance(argname, str) else argname
        if len(argnames) > 1:
            ids = [
                "-".join(f"{k}={v}" for k, v in zip(argnames, p_argvalues))
                for p_argvalues in argvalues
            ]
        else:
            ids = [f"{argnames[0]}={v}" for v in argvalues]
    return pytest.mark.parametrize(
        argname, argvalues, indirect=indirect, ids=ids, scope=scope
    )
