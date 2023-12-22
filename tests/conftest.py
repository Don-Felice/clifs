"""Common pytest fixtures"""


import shutil
from pathlib import Path

import pytest

from tests.common.utils_testing import get_files, update_mtime


@pytest.fixture(scope="function")
def dir_testrun(tmp_path: Path):
    # create source dest structure for update test
    shutil.copytree(Path(__file__).parent / "common" / "data", tmp_path / "data")
    return tmp_path


@pytest.fixture(scope="function")
def dirs_source(dir_testrun, num_dirs=2):
    dirs_res = [
        (dir_testrun / "data" / ("dir_source_" + str(i)))
        for i in range(1, num_dirs + 1)
    ]
    # update some files to check mtime consistency
    for dir in dirs_res:
        for file in get_files(dir):
            if "2" in file.stem:
                update_mtime(file)
    return dirs_res


@pytest.fixture(scope="function")
def dirs_dest(dir_testrun, num_dirs=2):
    return [
        (dir_testrun / "data" / ("dir_dest_" + str(i))) for i in range(1, num_dirs + 1)
    ]


@pytest.fixture(scope="function")
def dirs_flatten_dir_source_ref(dir_testrun, num_dirs=2):
    return [
        (dir_testrun / "data" / ("ref_flatten_dir_source_" + str(i)))
        for i in range(1, num_dirs + 1)
    ]


@pytest.fixture(scope="function")
def dirs_keep_dir_source2dest_ref(dir_testrun, num_dirs=2):
    return [
        (dir_testrun / "data" / ("ref_keep_dir_source2dest_" + str(i)))
        for i in range(1, num_dirs + 1)
    ]


@pytest.fixture(scope="function")
def dirs_source_ref(dirs_source):
    # create source reference to check source dir integrity
    dirs_res = []
    for dir in dirs_source:
        dir_res = dir.parent / (dir.name + "_ref")
        shutil.copytree(dir, dir_res)
        dirs_res.append(dir_res)
    return dirs_res


@pytest.fixture(scope="function")
def dirs_dest_ref(dirs_dest):
    # create source reference to check source dir integrity
    dirs_res = []
    for dir in dirs_dest:
        dir_res = dir.parent / (dir.name + "_ref")
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
