"""Test the path getter mixin class"""


import os
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from clifs.utils_fs import PathGetterMixin
from tests.common.utils_testing import parametrize_default_ids


@parametrize_default_ids("filter_str", [".txt", "2", ""])
@parametrize_default_ids("recursive", [True, False])
@parametrize_default_ids(
    ["path_filterlist", "header_filterlist", "sep_filterlist"],
    [
        (None, None, None),
        ("path_filterlist_txt", None, None),
        ("path_filterlist_csv", "filter", ","),
        ("path_filterlist_tsv", "filter", "\t"),
    ],
)
def test_path_getter(
    dirs_source,
    recursive,
    filter_str,
    path_filterlist,
    header_filterlist,
    sep_filterlist,
    request,
):
    for dir in dirs_source:
        # run the actual function to test
        path_getter = PathGetterMixin()

        path_getter.dir_source = dir
        path_getter.recursive = recursive
        path_getter.filterlist = (
            path_filterlist
            if path_filterlist is None
            else request.getfixturevalue(path_filterlist)
        )
        path_getter.filterlistheader = header_filterlist
        path_getter.filterlistsep = sep_filterlist
        path_getter.filterstring = filter_str

        files_found, dirs_found = path_getter.get_paths()

        pattern = f"*{filter_str}*" if filter_str else "*"

        if path_filterlist is None:
            if recursive:
                assert files_found == [x for x in dir.rglob(pattern) if not x.is_dir()]
                assert dirs_found == [x for x in dir.rglob(pattern) if x.is_dir()]
            else:
                assert files_found == [x for x in dir.glob(pattern) if not x.is_dir()]
                assert dirs_found == [x for x in dir.glob(pattern) if x.is_dir()]

        else:
            exp_files = ["L1_file_2.txt", "L2_file_1.txt", "L3_file_3.txt"]
            exp_dirs = ["subdir_1"]
            if recursive:
                assert files_found == [
                    x
                    for x in dir.rglob(pattern)
                    if not x.is_dir() and x.name in exp_files
                ]
                assert dirs_found == [
                    x for x in dir.rglob(pattern) if x.is_dir() and x.name in exp_dirs
                ]
            else:
                assert files_found == [
                    x
                    for x in dir.glob(pattern)
                    if not x.is_dir() and x.name in exp_files
                ]
                assert dirs_found == [
                    x for x in dir.glob(pattern) if x.is_dir() and x.name in exp_dirs
                ]


@parametrize_default_ids("now_stamp", [1e9, datetime.now().timestamp()])
@parametrize_default_ids("quantity", [1, 7, 12])
@parametrize_default_ids("unit", ["s", "min", "h", "mon", "a", "y", "d", ""])
def test_time_parsing(quantity, unit, now_stamp):
    now = datetime.fromtimestamp(now_stamp)

    path_getter = PathGetterMixin()
    th_stamp = path_getter._get_time_threshold(str(quantity) + unit, now=now)

    if unit == "s":
        assert th_stamp == now_stamp - quantity
    elif unit == "min":
        assert th_stamp == now_stamp - quantity * 60
    elif unit == "h":
        assert th_stamp == now_stamp - quantity * 60 * 60
    elif unit == "" or unit == "d":
        assert th_stamp == now_stamp - quantity * 60 * 60 * 24
    elif unit == "mon":
        th_year = now.year - quantity // 12
        th_month = now.month - quantity % 12
        if th_month < 1:
            th_month += 12
            th_year -= 1
        assert th_stamp == now.replace(year=th_year, month=th_month).timestamp()
    elif unit == "a" or unit == "y":
        assert th_stamp == now.replace(year=now.year - quantity).timestamp()


DELTA = 15


@parametrize_default_ids("mtime_stamp_older", [DELTA - 10, DELTA + 10])
@parametrize_default_ids("mtime_stamp_newer", [DELTA - 10, DELTA + 10])
@parametrize_default_ids("ctime_stamp_older", [DELTA - 10, DELTA + 10])
@parametrize_default_ids("ctime_stamp_newer", [DELTA - 10, DELTA + 10])
def test_time_filters(
    dirs_source,
    mtime_stamp_older,
    mtime_stamp_newer,
    ctime_stamp_older,
    ctime_stamp_newer,
):
    dir = dirs_source[0]

    # we test for days unit
    unit = "d"
    time_stamp = time.time() - DELTA * 60 * 60 * 24

    with patch.object(os.stat_result, "st_ctime", time_stamp), patch.object(
        os.stat_result, "st_mtime", time_stamp
    ):
        path_getter = PathGetterMixin()

        path_getter.dir_source = dir
        path_getter.recursive = True
        path_getter.filterlist = None
        path_getter.filterlistheader = None
        path_getter.filterlistsep = None
        path_getter.filterstring = None

        path_getter.mtime_stamp_older = str(mtime_stamp_older) + unit
        path_getter.mtime_stamp_newer = str(mtime_stamp_newer) + unit
        path_getter.ctime_stamp_older = str(ctime_stamp_older) + unit
        path_getter.ctime_stamp_newer = str(ctime_stamp_newer) + unit

        files_found, dirs_found = path_getter.get_paths()

        if (
            float(mtime_stamp_older) > DELTA
            or float(mtime_stamp_newer) < DELTA
            or float(ctime_stamp_older) > DELTA
            or float(ctime_stamp_newer) < DELTA
        ):
            assert files_found == []
            assert dirs_found == []
        else:
            assert set(files_found) == set(
                x.resolve() for x in dir.rglob("*") if not x.is_dir()
            )
            assert set(dirs_found) == set(
                x.resolve() for x in dir.rglob("*") if x.is_dir()
            )
