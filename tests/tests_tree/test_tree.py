"""Test the tree plugin"""


import re
from argparse import Namespace
from unittest.mock import patch

import pytest

from clifs.__main__ import main
from clifs.plugins.tree import DirectoryTree
from tests.common.utils_testing import escape_rich_style, parametrize_default_ids


@pytest.fixture()
def trees_source_dir():
    dir_1_tree = (
        "dir_source_1    7.00 KB\n"
        "├── L1_file_1.txt    1.00 KB\n"
        "├── L1_file_2.txt    1.00 KB\n"
        "├── subdir_1    4.00 KB\n"
        "│   ├── L2_file_1.txt    1.00 KB\n"
        "│   └── subsubdir_1    3.00 KB\n"
        "│       ├── L3_file_1.txt    1.00 KB\n"
        "│       ├── L3_file_2.txt    1.00 KB\n"
        "│       └── L3_file_3.txt    1.00 KB\n"
        "└── subdir_2    1.00 KB\n"
        "    └── L2_file_2.txt    1.00 KB\n"
    )

    dir_2_tree = (
        "dir_source_2    8.00 KB\n"
        "├── L1_file_1.txt    1.00 KB\n"
        "├── L1_file_2.txt    1.00 KB\n"
        "├── L1_file_3.txt    1.00 KB\n"
        "├── subdir_1    4.00 KB\n"
        "│   ├── L2_file_1.txt    1.00 KB\n"
        "│   └── subsubdir_1    3.00 KB\n"
        "│       ├── L3_file_1.txt    1.00 KB\n"
        "│       ├── L3_file_2.txt    1.00 KB\n"
        "│       └── L3_file_3.txt    1.00 KB\n"
        "└── subdir_2    1.00 KB\n"
        "    └── L2_file_2.txt    1.00 KB\n"
    )
    return (dir_1_tree, dir_2_tree)


@parametrize_default_ids("dirs_only", [False, True])
@parametrize_default_ids("hide_sizes", [False, True])
@parametrize_default_ids("depth", [None, 1, 2])
def test_tree(dirs_source, trees_source_dir, dirs_only, hide_sizes, depth):
    for idx, folder in enumerate(dirs_source):
        with patch("os.stat_result.st_size", 1024):
            tree = DirectoryTree(
                Namespace(
                    root_dir=folder,
                    dirs_only=dirs_only,
                    hide_sizes=hide_sizes,
                    depth=depth,
                )
            )
        tree.run()
        print(f"Tree generation for {folder.name} went through.")

        exp_tree = trees_source_dir[idx].splitlines()
        if depth is not None:
            for idx, line in enumerate(exp_tree.copy()):
                if match := re.match(r".*L(\d+)_file.*", line):
                    exp_depth = int(match[1])
                else:
                    exp_depth = len(re.findall("sub", line))
                if exp_depth > depth:
                    exp_tree.remove(line)
        if dirs_only:
            for line in exp_tree.copy():
                if "dir" not in line:
                    exp_tree.remove(line)
        if hide_sizes:
            exp_tree_no_sizes = []
            for line in exp_tree:
                exp_tree_no_sizes.append(line[:-9].rstrip())
            exp_tree = exp_tree_no_sizes

        act_tree = tree.__str__().splitlines()
        for lineidx, line in enumerate(act_tree):
            try:
                assert escape_rich_style(line) == exp_tree[lineidx].replace(
                    "\n", ""
                ), f"Trees for {folder} are not identical."
            except AssertionError:
                print(f"{exp_tree=}")
                print(f"{act_tree=}")
                raise


def test_entry(dirs_source, capfd, trees_source_dir):
    for dir, exp_tree in zip(dirs_source, trees_source_dir):
        # run the actual function to test
        with patch("sys.argv", ["clifs", "tree", str(dir)]), patch(
            "os.stat_result.st_size", 1024
        ):
            main()
        out, _ = capfd.readouterr()
        for line in exp_tree.splitlines():
            assert line in out, (
                "Expected the following line in the output but did not find it:\n"
                f"{line}"
            )
