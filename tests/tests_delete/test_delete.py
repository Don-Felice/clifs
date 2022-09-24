# -*- coding: utf-8 -*-


from argparse import Namespace
from pathlib import Path
import shutil


import pytest

from clifs.plugins.delete import FileDeleter
from tests.common.utils_testing import substr_in_dir_names, parametrize_default_ids


@pytest.fixture(scope="function")
def dir_testrun(tmp_path: Path):
    # create source dest structure for update test
    shutil.copytree(Path(__file__).parents[1] / "common" / "data", tmp_path / "data")
    return tmp_path


@pytest.fixture(scope="function")
def dirs_dest(dir_testrun, num_dirs=2):
    return [
        (dir_testrun / "data" / ("dir_dest_" + str(i))) for i in range(1, num_dirs + 1)
    ]


@parametrize_default_ids("filter_str", ["DELME", "file"])
def test_delete(dirs_dest, filter_str):
    # run the actual function to test

    for dir in dirs_dest:
        deleter = FileDeleter(
            Namespace(
                dir_source=dir,
                recursive=True,
                filterlist=None,
                filterlistheader=None,
                filterlistsep=None,
                filterstring=None,
                skip_preview=True,
            )
        )
        deleter.run()
        print(f"Delete of {dir.name} went through.")

        assert not substr_in_dir_names(dir, sub_str=filter_str, files_only=True)
