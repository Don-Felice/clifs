# -*- coding: utf-8 -*-

from unittest.mock import patch

from clifs.__main__ import main
from tests.common.utils_testing import (
    assert_files_present,
    parametrize_default_ids,
    substr_in_dir_names,
)


@parametrize_default_ids(
    ("pattern", "replacement"), [("file", "SUBSTITUTE"), (".txt", "123456")]
)
def test_rename(dirs_source, dirs_source_ref, pattern, replacement):
    # run the actual function to test

    for idx_dir, dir in enumerate(dirs_source):
        patch_args = [
            "clifs",
            "ren",
            str(dir),
            "--pattern",
            pattern,
            "--replacement",
            replacement,
            "--recursive",
        ]
        with patch("sys.argv", patch_args), patch("builtins.input", return_value="yes"):
            main()

        print(f"Renaming of {dir.name} went through.")

        assert not substr_in_dir_names(dir, sub_str=pattern, files_only=True)

        # revert and check conistency
        patch_args = [
            "clifs",
            "ren",
            str(dir),
            "--pattern",
            replacement,
            "--replacement",
            pattern,
            "--recursive",
            "--skip_preview",
        ]
        with patch("sys.argv", patch_args):
            main()

        print(f"Re-renaming of {dir.name} went through.")

        assert not substr_in_dir_names(dir, sub_str=replacement, files_only=True)

        assert_files_present(dir_source=dirs_source_ref[idx_dir], dir_ref=dir)
