# -*- coding: utf-8 -*-


from argparse import Namespace
from functools import partial
from pathlib import Path
import shutil


import pytest

from clifs.plugins.como import FileCopier, FileMover
from tests.common.utils_testing import compare_files, parametrize_default_ids


def contains_delme(directory):
    return any(["DELME" in str(x) for x in directory.rglob("*")])


@pytest.fixture(scope="function")
def dir_testrun(tmp_path: Path):
    # create source dest structure for update test
    shutil.copytree(Path(__file__).parents[1] / "common" / "data", tmp_path / "data")

    # update some files to change mtime
    path_updateme = (
        tmp_path
        / "data"
        / "dir_source_1"
        / "subdir_1"
        / "subsubdir_1"
        / "L3_file_1.txt"
    )
    with path_updateme.open("a") as filetoupdate:
        filetoupdate.write("I have been updated.")

    # create source reference to check source dir integrity
    shutil.copytree(
        tmp_path / "data" / "dir_source_1", tmp_path / "data" / "dir_source_1_ref"
    )
    shutil.copytree(
        tmp_path / "data" / "dir_source_2", tmp_path / "data" / "dir_source_2_ref"
    )

    # create dest reference for check dest dir integrity after dry run
    shutil.copytree(
        tmp_path / "data" / "dir_dest_1", tmp_path / "data" / "dir_dest_1_ref"
    )
    shutil.copytree(
        tmp_path / "data" / "dir_dest_2", tmp_path / "data" / "dir_dest_2_ref"
    )

    # create empty dest folders for flattening
    (tmp_path / "data" / "dir_dest_empty_1").mkdir()
    (tmp_path / "data" / "dir_dest_empty_2").mkdir()
    return tmp_path


@pytest.fixture(scope="function")
def dir_pairs(dir_testrun, num_dirs=2):
    dir_pairs = {}
    dir_pairs["source_dest"] = [
        (
            dir_testrun / "data" / ("dir_source_" + str(i)),
            dir_testrun / "data" / ("dir_dest_" + str(i)),
        )
        for i in range(1, num_dirs + 1)
    ]
    dir_pairs["source_ref"] = [
        (
            dir_testrun / "data" / ("dir_source_" + str(i)),
            dir_testrun / "data" / ("dir_source_" + str(i) + "_ref"),
        )
        for i in range(1, num_dirs + 1)
    ]
    dir_pairs["dest_ref"] = [
        (
            dir_testrun / "data" / ("dir_dest_" + str(i)),
            dir_testrun / "data" / ("dir_dest_" + str(i) + "_ref"),
        )
        for i in range(1, num_dirs + 1)
    ]
    dir_pairs["emptydest_refsourceflat"] = [
        (
            dir_testrun / "data" / ("dir_dest_empty_" + str(i)),
            dir_testrun / "data" / ("ref_flatten_dir_source_" + str(i)),
        )
        for i in range(1, num_dirs + 1)
    ]
    dir_pairs["source_refkeepsource2dest"] = [
        (
            dir_testrun / "data" / ("dir_source_" + str(i)),
            dir_testrun / "data" / ("ref_keep_dir_source2dest_" + str(i)),
        )
        for i in range(1, num_dirs + 1)
    ]
    dir_pairs["source_emptydest"] = [
        (
            dir_testrun / "data" / ("dir_source_" + str(i)),
            dir_testrun / "data" / ("dir_dest_empty_" + str(i)),
        )
        for i in range(1, num_dirs + 1)
    ]
    return dir_pairs


@parametrize_default_ids(
    ["skip_existing", "keep_all"], [(False, True), (True, False), (False, False)]
)
@parametrize_default_ids("dryrun", [False, True])
@parametrize_default_ids("flatten", [False, True])
def test_copy(dir_pairs, dryrun, skip_existing, keep_all, flatten):
    # run the actual function to test
    test_pair = "source_emptydest" if flatten else "source_dest"

    for dir_pair in dir_pairs[test_pair]:
        copier = FileCopier(
            Namespace(
                dir_source=dir_pair[0],
                dir_dest=dir_pair[1],
                recursive=True,
                filterlist=None,
                filterlistheader=None,
                filterlistsep=None,
                filterstring=None,
                skip_existing=skip_existing,
                keep_all=False,
                flatten=flatten,
                dryrun=dryrun,
            )
        )
        copier.run()
    print("Copy went through.")

    if not dryrun:
        # check for proper updating and deleting
        if flatten:
            for dir_pair in dir_pairs["emptydest_refsourceflat"]:
                compare_files(*dir_pair, check_mtime=False)
        elif keep_all:
            for dir_pair in dir_pairs["source_refkeepsource2dest"]:
                compare_files(*dir_pair, check_mtime=False)
        else:
            for dir_pair in dir_pairs["source_dest"]:
                compare_files(*dir_pair, check_mtime=not skip_existing)
    else:
        # check for dest dir integrity
        for dir_pair in dir_pairs["dest_ref"]:
            compare_files(*dir_pair)

    # check for source dir integrity
    for dir_pair in dir_pairs["source_ref"]:
        compare_files(*dir_pair)


@parametrize_default_ids(
    "skip_existing, keep_all", [(False, True), (True, False), (False, False)]
)
@parametrize_default_ids("dryrun", [False, True])
@parametrize_default_ids("flatten", [False, True])
def test_move(dir_pairs, dryrun, skip_existing, keep_all, flatten):
    # run the actual function to test
    test_pair = "source_emptydest" if flatten else "source_dest"

    for dir_pair in dir_pairs[test_pair]:
        mover = FileMover(
            Namespace(
                dir_source=dir_pair[0],
                dir_dest=dir_pair[1],
                recursive=True,
                filterlist=None,
                filterlistheader=None,
                filterlistsep=None,
                filterstring=None,
                skip_existing=skip_existing,
                keep_all=False,
                flatten=flatten,
                dryrun=dryrun,
            )
        )
        mover.run()
    print("Copy went through.")

    if not dryrun:
        # check for proper updating and deleting
        if flatten:
            for dir_pair in dir_pairs["emptydest_refsourceflat"]:
                compare_files(*dir_pair, check_mtime=False)
        elif keep_all:
            for dir_pair in dir_pairs["source_refkeepsource2dest"]:
                compare_files(*dir_pair, check_mtime=False)
        else:
            for dir_pair in dir_pairs["source_dest"]:
                compare_files(*dir_pair, check_mtime=not skip_existing)
    else:
        # check for dest dir integrity
        for dir_pair in dir_pairs["dest_ref"]:
            compare_files(*dir_pair)

        # check for source dir integrity
        for dir_pair in dir_pairs["source_ref"]:
            compare_files(*dir_pair)
