"""Test the rename plugin"""

from unittest.mock import patch

from clifs.__main__ import main
from tests.common.utils_testing import (
    assert_files_present,
    parametrize_default_ids,
    substr_in_dir_names,
)


@parametrize_default_ids(
    ("pattern", "replacement"),
    [("file", "SUBSTITUTE"), (".txt", "123456"), ("dir", "folder")],
)
@parametrize_default_ids("dirs", [False, True])
def test_rename(dirs_source, dirs_source_ref, pattern, replacement, dirs):
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
        if dirs:
            patch_args.append("--dirs")
        with patch("sys.argv", patch_args), patch("builtins.input", return_value="yes"):
            main()

        print(f"Renaming of {dir.name} went through.")

        if not dirs:
            assert not substr_in_dir_names(dir, sub_str=pattern, files_only=True)
        else:
            assert not substr_in_dir_names(dir, sub_str=pattern, dirs_only=True)

        # revert and check consistency
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
        if dirs:
            patch_args.append("--dirs")
        with patch("sys.argv", patch_args):
            main()

        print(f"Re-renaming of {dir.name} went through.")

        if not dirs:
            assert not substr_in_dir_names(dir, sub_str=replacement, files_only=True)
        else:
            assert not substr_in_dir_names(dir, sub_str=replacement, dirs_only=True)

        assert_files_present(dir_source=dirs_source_ref[idx_dir], dir_ref=dir)


@parametrize_default_ids("dirs", [False, True])
def test_reject_bad_chars(dirs_source, dirs_source_ref, dirs):
    # run the actual function to test
    bad_char = "~"

    for idx_dir, dir in enumerate(dirs_source):
        patch_args = [
            "clifs",
            "ren",
            str(dir),
            "--pattern",
            "1",
            "--replacement",
            bad_char,
            "--recursive",
        ]
        if dirs:
            patch_args.append("--dirs")
        with patch("sys.argv", patch_args), patch("builtins.input", return_value="yes"):
            main()

        print(f"Renaming of {dir.name} went through.")

        if not dirs:
            assert not substr_in_dir_names(dir, sub_str=bad_char, files_only=True)
        else:
            assert not substr_in_dir_names(dir, sub_str=bad_char, dirs_only=True)

        assert_files_present(dir_source=dirs_source_ref[idx_dir], dir_ref=dir)


@parametrize_default_ids(
    ("dirs", "pattern", "replacement"),
    [(False, "L1_file_1", "L1_file_2"), (True, "subdir_1", "subdir_2")],
)
def test_suffix_duplicates(dirs_source, dirs, pattern, replacement):
    for dir in dirs_source:
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
        if dirs:
            patch_args.append("--dirs")
        with patch("sys.argv", patch_args), patch("builtins.input", return_value="yes"):
            main()

        print(f"Renaming of {dir.name} went through.")

        assert f"{replacement} (2)" in [x.stem for x in dir.rglob("*")]
