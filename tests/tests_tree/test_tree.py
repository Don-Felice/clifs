# -*- coding: utf-8 -*-


from argparse import Namespace
from unittest.mock import patch

import pytest

from clifs.__main__ import main
from clifs.plugins.tree import DirectoryTree
from tests.common.utils_testing import escape_ansi, parametrize_default_ids


@pytest.fixture()
def trees_source_dir():
    dir_1_tree = (
        "dir_source_1    0.01 MB\n"
        "├── L1_file_1.txt    0.01 MB\n"
        "├── L1_file_2.txt    0.00 MB\n"
        "├──subdir_1    0.00 MB\n"
        "│   ├── L2_file_1.txt    0.00 MB\n"
        "│   └──subsubdir_1    0.00 MB\n"
        "│       ├── L3_file_1.txt    0.00 MB\n"
        "│       ├── L3_file_2.txt    0.00 MB\n"
        "│       └── L3_file_3.txt    0.00 MB\n"
        "└──subdir_2    0.00 MB\n"
        "    └── L2_file_2.txt    0.00 MB"
    )

    dir_2_tree = (
        "dir_source_2    0.01 MB\n"
        "├── L1_file_1.txt    0.00 MB\n"
        "├── L1_file_2.txt    0.00 MB\n"
        "├── L1_file_3.txt    0.00 MB\n"
        "├──subdir_1    0.01 MB\n"
        "│   ├── L2_file_1.txt    0.00 MB\n"
        "│   └──subsubdir_1    0.01 MB\n"
        "│       ├── L3_file_1.txt    0.00 MB\n"
        "│       ├── L3_file_2.txt    0.01 MB\n"
        "│       └── L3_file_3.txt    0.00 MB\n"
        "└──subdir_2    0.00 MB\n"
        "    └── L2_file_2.txt    0.00 MB\n"
    )
    return (dir_1_tree, dir_2_tree)


@parametrize_default_ids("dirs_only", [False, True])
@parametrize_default_ids("hide_sizes", [False, True])
def test_tree(dirs_source, trees_source_dir, dirs_only, hide_sizes):

    for idx, folder in enumerate(dirs_source):
        tree = DirectoryTree(
            Namespace(
                root_dir=folder,
                dirs_only=dirs_only,
                hide_sizes=hide_sizes,
            )
        )
        tree.run()
        print(f"Tree generation for {folder.name} went through.")

        exp_tree = trees_source_dir[idx].splitlines()
        if dirs_only:
            for line in exp_tree.copy():
                if "dir" not in line:
                    exp_tree.remove(line)
        if hide_sizes:
            exp_tree_no_sizes = []
            for line in exp_tree:
                exp_tree_no_sizes.append(line[:-9].rstrip())
            exp_tree = exp_tree_no_sizes

        for lineidx, line in enumerate(tree._tree):
            print(exp_tree[lineidx])
            assert escape_ansi(tree._tree[lineidx]) == exp_tree[lineidx].replace(
                "\n", ""
            ), f"Trees for {folder} are not identical."


def test_entry(dirs_source, capfd, trees_source_dir):
    for dir, exp_tree in zip(dirs_source, trees_source_dir):
        # run the actual function to test
        with patch("sys.argv", ["clifs", "tree", str(dir)]):
            main()
        out, err = capfd.readouterr()
        for line in exp_tree.splitlines():
            assert line in out, (
                "Expected the following line in the output but did not find it:\n"
                f"{line}"
            )
