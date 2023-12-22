"""Test the disc usage plugin"""


import re
from argparse import Namespace
from unittest.mock import patch

from clifs.__main__ import main
from clifs.plugins.disc_usage import DiscUsageExplorer
from tests.common.utils_testing import escape_rich_style, parametrize_default_ids


@parametrize_default_ids("usage_info", [(1000, 400, 600), (100000, 70000, 30000)])
def test_disc_usage_numbers(dirs_empty, usage_info):
    # run the actual function to test
    with patch("shutil.disk_usage", return_value=(usage_info)):
        usage_explorer = DiscUsageExplorer(
            Namespace(
                dirs=[str(x) for x in dirs_empty],
            )
        )

    for dir in dirs_empty:
        space_total = usage_explorer._dict_usage[str(dir)].total
        space_used = usage_explorer._dict_usage[str(dir)].used
        space_free = usage_explorer._dict_usage[str(dir)].free

        assert (
            space_total == usage_info[0]
        ), f"Total disc space does not match: exp={usage_info[0]}, act={space_total}"
        assert (
            space_used == usage_info[1]
        ), f"Used disc space does not match: exp={usage_info[1]}, act={space_used}"
        assert (
            space_free == usage_info[2]
        ), f"Total disc space does not match: exp={usage_info[2]}, act={space_free}"


@parametrize_default_ids("usage_info", [(1000, 400, 600), (100000, 70000, 30000)])
def test_disc_usage_output(dirs_empty, usage_info, capfd):
    # run the actual function to test
    with patch("sys.argv", ["clifs", "du"] + [str(x) for x in dirs_empty]), patch(
        "shutil.disk_usage", return_value=(usage_info)
    ):
        main()

    captured = capfd.readouterr()
    for sp_type, sp_val in zip(["total", "used", "free"], usage_info):
        assert len(
            re.findall(
                rf"{sp_type}: *{sp_val / 1024:.2f} KB", escape_rich_style(captured.out)
            )
        ) == len(dirs_empty)
    perc_used = round(100.0 * usage_info[1] / float(usage_info[0]), 1)
    assert len(re.findall(rf"{perc_used:5}%", escape_rich_style(captured.out))) == len(
        dirs_empty
    )
