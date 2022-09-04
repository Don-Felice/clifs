# -*- coding: utf-8 -*-

# test folder backup

from argparse import Namespace
import os
from pathlib import Path
import shutil


import pytest

from clifs.plugins.backup import FileSaver


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


def check_mtime_consistency(file1, file2):
    assert (
        abs(os.path.getmtime(file1) - os.path.getmtime(file2)) <= 1
    ), f"File modification time is not consistent for file {file1}"


def compare_files(dir_source, dir_ref):
    print("---------------------")
    print(
        f"checking consistencies of folders:"
        f"\n{str(dir_source)}\nand\n{str(dir_ref)}."
    )
    list_files_source = [x for x in dir_source.rglob("*") if not x.is_dir()]
    for cur_file_source in list_files_source:
        cur_file_dest = Path(
            str(cur_file_source).replace(str(dir_source), str(dir_ref))
        )
        print(f"checking file: {cur_file_source}")
        # check for existence
        assert (
            cur_file_dest.exists()
        ), f"file {cur_file_source.name} from {dir_source} not existent in {dir_ref}."
        # check for proper updating
        check_mtime_consistency(cur_file_source, cur_file_dest)
    print("---------------------")


def contains_delme(directory):
    return any(["DELME" in str(x) for x in directory.rglob("*")])


@pytest.fixture(scope="function")
def dir_testrun(tmp_path: Path):
    # create source dest structure for update test
    shutil.copytree(Path(__file__).parent / "data", tmp_path / "data")

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
    return dir_pairs


@pytest.fixture(scope="function")
def cfg_testrun(dir_testrun):
    path_cfg_template = Path(__file__).parent / "cfg_template.csv"
    path_cfg_test = create_test_cfg(path_cfg_template, dir_testrun)
    return path_cfg_test


@pytest.mark.parametrize("from_cfg", [(False), (True)])
@pytest.mark.parametrize("delete", [(False), (True)])
@pytest.mark.parametrize("dry_run", [(False), (True)])
def test_backup(cfg_testrun, dir_pairs, from_cfg, delete, dry_run):
    # run the actual function to test
    if from_cfg:
        saver = FileSaver(
            Namespace(
                cfg_file=cfg_testrun,
                dir_source=None,
                dir_dest=None,
                delete=delete,
                dry_run=dry_run,
            )
        )
        saver.run()
    else:
        for dir_pair in dir_pairs["source_dest"]:
            saver = FileSaver(
                Namespace(
                    cfg_file=None,
                    dir_source=str(dir_pair[0]),
                    dir_dest=str(dir_pair[1]),
                    delete=delete,
                    dry_run=dry_run,
                )
            )
            saver.run()
    print("Backup went through.")

    if not dry_run:
        # check for proper updating and deleting
        for dir_pair in dir_pairs["source_dest"]:
            compare_files(*dir_pair)
            if delete:
                assert not contains_delme(
                    dir_pair[1]
                ), "Files only present in destination dir have not been deleted."
            else:
                assert contains_delme(
                    dir_pair[1]
                ), "Files only present in destination dir have been deleted."

    # check for source dir integrity
    for dir_pair in dir_pairs["source_ref"]:
        compare_files(*dir_pair)

    if dry_run:
        # check for dest dir integrity
        for dir_pair in dir_pairs["dest_ref"]:
            compare_files(*dir_pair)
