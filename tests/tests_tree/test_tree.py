# -*- coding: utf-8 -*-


from argparse import Namespace
import os
from pathlib import Path
import re
import shutil
from typing import List


import pytest

from clifs.plugins.tree import DirectoryTree
from tests.common.utils_testing import (
    escape_ansi,
    parametrize_default_ids,
    read_lines_from_file,
)


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
def data_paths(dir_testrun, num_dirs=2):
    paths = {}
    paths["source_dirs"] = [
        dir_testrun / "data" / ("dir_source_" + str(i)) for i in range(1, num_dirs + 1)
    ]
    paths["source_dir_trees"] = [
        dir_testrun / "data" / ("tree_dir_source_" + str(i) + ".txt")
        for i in range(1, num_dirs + 1)
    ]
    return paths


@parametrize_default_ids("dirs_only", [False, True])
@parametrize_default_ids("hide_sizes", [False, True])
def test_copy(data_paths, dirs_only, hide_sizes):

    for idx, folder in enumerate(data_paths["source_dirs"]):
        tree = DirectoryTree(
            Namespace(
                root_dir=folder,
                dirs_only=dirs_only,
                hide_sizes=hide_sizes,
            )
        )
        tree.run()
        print(f"Tree generation for {folder.name} went through.")

        ref_tree = read_lines_from_file(data_paths["source_dir_trees"][idx])
        if dirs_only:
            for line in ref_tree.copy():
                if "dir" not in line:
                    ref_tree.remove(line)
        if hide_sizes:
            ref_tree_no_sizes = []
            for line in ref_tree:
                ref_tree_no_sizes.append(line[:-9].rstrip())
            ref_tree = ref_tree_no_sizes

        for lineidx, line in enumerate(tree._tree):
            print(ref_tree[lineidx])
            assert escape_ansi(tree._tree[lineidx]) == ref_tree[lineidx].replace(
                "\n", ""
            ), f"Trees for {folder} are not identical."
