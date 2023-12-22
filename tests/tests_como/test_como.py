"""Test the copy and move plugins"""


from unittest.mock import patch

from clifs.__main__ import main
from tests.common.utils_testing import assert_files_present, parametrize_default_ids


@parametrize_default_ids(
    ["skip_existing", "keep_all"], [(False, True), (True, False), (False, False)]
)
@parametrize_default_ids("dryrun", [False, True])
@parametrize_default_ids("flatten", [False, True])
def test_copy(
    dirs_source,
    dirs_dest,
    dirs_source_ref,
    dirs_dest_ref,
    dirs_empty,
    dirs_flatten_dir_source_ref,
    dirs_keep_dir_source2dest_ref,
    dryrun,
    skip_existing,
    keep_all,
    flatten,
):
    n_test_dirs = len(dirs_source)
    # run the actual function to test
    for idx_dir in range(n_test_dirs):
        patch_args = [
            "clifs",
            "cp",
            str(dirs_source[idx_dir]),
            str(dirs_empty[idx_dir] if flatten else dirs_dest[idx_dir]),
            "--recursive",
        ]

        if skip_existing:
            patch_args.append("--skip_existing")
        if keep_all:
            patch_args.append("--keep_all")
        if flatten:
            patch_args.append("--flatten")
        if dryrun:
            patch_args.append("--dryrun")

        with patch("sys.argv", patch_args):
            main()
    print("Copy went through.")

    if not dryrun:
        # check for proper updating and deleting
        if flatten:
            for idx_dir in range(n_test_dirs):
                assert_files_present(
                    dirs_empty[idx_dir],
                    dirs_flatten_dir_source_ref[idx_dir],
                    check_mtime=False,
                )
                assert_files_present(
                    dirs_flatten_dir_source_ref[idx_dir],
                    dirs_empty[idx_dir],
                    check_mtime=False,
                )
        elif keep_all:
            for idx_dir in range(n_test_dirs):
                assert_files_present(
                    dirs_keep_dir_source2dest_ref[idx_dir],
                    dirs_dest[idx_dir],
                    check_mtime=False,
                )
                assert_files_present(
                    dirs_dest[idx_dir],
                    dirs_keep_dir_source2dest_ref[idx_dir],
                    check_mtime=False,
                )
        else:
            for idx_dir in range(n_test_dirs):
                assert_files_present(
                    dirs_source[idx_dir],
                    dirs_dest[idx_dir],
                    check_mtime=not skip_existing,
                )
    else:
        # check for dest dir integrity
        for idx_dir in range(n_test_dirs):
            assert_files_present(dirs_dest[idx_dir], dirs_dest_ref[idx_dir])

    # check for source dir integrity
    for idx_dir in range(n_test_dirs):
        assert_files_present(dirs_source[idx_dir], dirs_source_ref[idx_dir])


@parametrize_default_ids(
    "skip_existing, keep_all", [(False, True), (True, False), (False, False)]
)
@parametrize_default_ids("dryrun", [False, True])
@parametrize_default_ids("flatten", [False, True])
def test_move(
    dirs_source,
    dirs_dest,
    dirs_source_ref,
    dirs_dest_ref,
    dirs_empty,
    dirs_flatten_dir_source_ref,
    dirs_keep_dir_source2dest_ref,
    dryrun,
    skip_existing,
    keep_all,
    flatten,
):
    # run the actual function to test
    n_test_dirs = len(dirs_source)
    # run the actual function to test
    for idx_dir in range(n_test_dirs):
        patch_args = [
            "clifs",
            "mv",
            str(dirs_source[idx_dir]),
            str(dirs_empty[idx_dir] if flatten else dirs_dest[idx_dir]),
            "--recursive",
        ]

        if skip_existing:
            patch_args.append("--skip_existing")
        if keep_all:
            patch_args.append("--keep_all")
        if flatten:
            patch_args.append("--flatten")
        if dryrun:
            patch_args.append("--dryrun")

        with patch("sys.argv", patch_args):
            main()
    print("Copy went through.")

    if not dryrun:
        # check for proper updating and deleting
        if flatten:
            for idx_dir in range(n_test_dirs):
                assert_files_present(
                    dirs_empty[idx_dir],
                    dirs_flatten_dir_source_ref[idx_dir],
                    check_mtime=False,
                )
                assert_files_present(
                    dirs_flatten_dir_source_ref[idx_dir],
                    dirs_empty[idx_dir],
                    check_mtime=False,
                )
        elif keep_all:
            for idx_dir in range(n_test_dirs):
                assert_files_present(
                    dirs_keep_dir_source2dest_ref[idx_dir],
                    dirs_dest[idx_dir],
                    check_mtime=False,
                )
                assert_files_present(
                    dirs_dest[idx_dir],
                    dirs_keep_dir_source2dest_ref[idx_dir],
                    check_mtime=False,
                )
        else:
            for idx_dir in range(n_test_dirs):
                assert_files_present(
                    dirs_source[idx_dir],
                    dirs_dest[idx_dir],
                    check_mtime=not skip_existing,
                )
    else:
        # check for dest dir integrity
        for idx_dir in range(n_test_dirs):
            assert_files_present(dirs_dest[idx_dir], dirs_dest_ref[idx_dir])

        # check for source dir integrity
        for idx_dir in range(n_test_dirs):
            assert_files_present(dirs_source[idx_dir], dirs_source_ref[idx_dir])
