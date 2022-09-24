import os
from pathlib import Path
import pytest
import re
import shutil


def read_lines_from_file(path_file):
    with path_file.open("r", encoding="utf-8") as file:
        lines = file.readlines()
    return lines


def escape_ansi(string):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", string)


def check_mtime_consistency(file1, file2):
    assert (
        abs(os.path.getmtime(file1) - os.path.getmtime(file2)) <= 1
    ), f"File modification time is not consistent for file {file1}"


def compare_files(dir_source, dir_ref, check_mtime=True):
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


def substr_in_dir_names(directory, sub_str="DELME", files_only=False):
    if files_only == True:
        return any([sub_str in x.name for x in directory.rglob("*") if x.is_file()])
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


@pytest.fixture(scope="function")
def dir_testrun(tmp_path: Path):
    # create source dest structure for update test
    shutil.copytree(Path(__file__).parents[1] / "common" / "data", tmp_path / "data")
    return tmp_path


@pytest.fixture(scope="function")
def dirs_source(dir_testrun, num_dirs=2):
    return [
        (dir_testrun / "data" / ("dir_source_" + str(i)))
        for i in range(1, num_dirs + 1)
    ]


@pytest.fixture(scope="function")
def dirs_dest(dir_testrun, num_dirs=2):
    return [
        (dir_testrun / "data" / ("dir_dest_" + str(i))) for i in range(1, num_dirs + 1)
    ]


@pytest.fixture(scope="function")
def dirs_source_ref(dirs_source):
    # create source reference to check source dir integrity
    dirs_res = []
    for dir in dirs_source:
        dir_res = dir.parent / (dir.name + "_ref")
        print(dir_res)
        shutil.copytree(dir, dir_res)
        dirs_res.append(dir_res)
    return dirs_res


@pytest.fixture(scope="function")
def dirs_empty(dir_testrun, num_dirs=2):
    lst_dirs = []
    for i in range(num_dirs):
        dir = dir_testrun / "data" / ("dir_empty_" + str(i + 1))
        dir.mkdir()
        lst_dirs.append(dir)
    return lst_dirs

@pytest.fixture(scope="function")
def path_filterlist_txt(dir_testrun):
    return dir_testrun / "data" / "list_filter.txt"

@pytest.fixture(scope="function")
def path_filterlist_csv(dir_testrun):
    return dir_testrun / "data" / "list_filter.csv"

@pytest.fixture(scope="function")
def path_filterlist_tsv(dir_testrun):
    return dir_testrun / "data" / "list_filter.tsv"