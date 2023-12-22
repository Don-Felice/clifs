"""Test the backup plugin"""


from pathlib import Path
from unittest.mock import patch

import pytest

from clifs.__main__ import main
from tests.common.utils_testing import (
    assert_files_present,
    parametrize_default_ids,
    substr_in_dir_names,
)


def create_test_cfg(path_cfg, path_output):
    path_cfg = Path(path_cfg)
    path_output = Path(path_output)

    with path_cfg.open("r") as file:
        text_cfg = file.read()

    text_cfg = text_cfg.replace("WHEREAMI", str(path_output))

    path_output = path_output / path_cfg.name
    with path_output.open("w") as file:
        file.write(text_cfg)
    return path_output


@pytest.fixture(scope="function")
def cfg_testrun(dir_testrun):
    path_cfg_template = Path(__file__).parent / "cfg_template.csv"
    path_cfg_test = create_test_cfg(path_cfg_template, dir_testrun)
    return path_cfg_test


@parametrize_default_ids("from_cfg", [False, True])
@parametrize_default_ids("delete", [False, True])
@parametrize_default_ids("dry_run", [False, True])
def test_backup(
    cfg_testrun,
    dirs_source,
    dirs_dest,
    dirs_source_ref,
    dirs_dest_ref,
    from_cfg,
    delete,
    dry_run,
):
    # run the actual function to test
    if from_cfg:
        patch_args = ["clifs", "backup", "--cfg_file", str(cfg_testrun)]
        if delete:
            patch_args.append("--delete")
        if dry_run:
            patch_args.append("--dry_run")

        with patch("sys.argv", patch_args):
            main()

    else:
        for idx_dir in range(len(dirs_source)):
            patch_args = [
                "clifs",
                "backup",
                "--dir_source",
                str(dirs_source[idx_dir]),
                "--dir_dest",
                str(dirs_dest[idx_dir]),
            ]
            if delete:
                patch_args.append("--delete")
            if dry_run:
                patch_args.append("--dry_run")

            with patch("sys.argv", patch_args):
                main()

    print("Backup went through.")

    if not dry_run:
        # check for proper updating and deleting
        for idx_dir in range(len(dirs_source)):
            assert_files_present(dirs_source[idx_dir], dirs_dest[idx_dir])
            if delete:
                assert not substr_in_dir_names(
                    dirs_dest[idx_dir]
                ), "Files only present in destination dir have not been deleted."
            else:
                assert substr_in_dir_names(
                    dirs_dest[idx_dir]
                ), "Files only present in destination dir have been deleted."
    else:
        # check for dest dir integrity
        for idx_dir in range(len(dirs_source)):
            assert_files_present(dirs_dest[idx_dir], dirs_dest_ref[idx_dir])

    # check for source dir integrity
    for idx_dir in range(len(dirs_source)):
        assert_files_present(dirs_source[idx_dir], dirs_source_ref[idx_dir])
