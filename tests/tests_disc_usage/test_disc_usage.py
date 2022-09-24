# -*- coding: utf-8 -*-


from argparse import Namespace
from math import isclose
from pathlib import Path
import re


from pytest_mock import mocker

from clifs.plugins.disc_usage import DiscUsageExplorer
from tests.common.utils_testing import (
    parametrize_default_ids,
    dirs_empty,
    dir_testrun,
    escape_ansi,
)


@parametrize_default_ids("usage_info", [(1000, 400, 600), (100000, 70000, 30000)])
def test_delete(dirs_empty, usage_info, mocker, capfd):
    mocker.patch("shutil.disk_usage", return_value=(usage_info))

    # run the actual function to test
    usage_explorer = DiscUsageExplorer(
        Namespace(
            dirs=[str(x) for x in dirs_empty],
        )
    )

    for idx_dir, dir in enumerate(dirs_empty, 1):

        space_total = usage_explorer._dict_usage[str(dir)]["total"]
        space_used = usage_explorer._dict_usage[str(dir)]["used"]
        space_free = usage_explorer._dict_usage[str(dir)]["free"]

        assert (
            space_total == usage_info[0]
        ), f"Total disc space does not match: exp={usage_info[0]}, act={space_total}"
        assert (
            space_used == usage_info[1]
        ), f"Used disc space does not match: exp={usage_info[1]}, act={space_used}"
        assert (
            space_free == usage_info[2]
        ), f"Total disc space does not match: exp={usage_info[2]}, act={space_free}"

    # test stdout
    usage_explorer._print_usage_info()
    captured = capfd.readouterr()
    for sp_type, sp_val in zip(["total", "used", "free"], usage_info):
        assert len(
            re.findall(
                rf"{sp_type}: *{sp_val / 10**6:.2f} MB", escape_ansi(captured.out)
            )
        ) == len(dirs_empty)
    perc_used = round(100.0 * usage_info[1] / float(usage_info[0]), 1)
    assert len(re.findall(rf"{perc_used:5}%", escape_ansi(captured.out))) == len(
        dirs_empty
    )
