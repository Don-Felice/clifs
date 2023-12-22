"""Test the delete plugin"""


from unittest.mock import patch

from clifs.__main__ import main
from tests.common.utils_testing import parametrize_default_ids, substr_in_dir_names


@parametrize_default_ids("filter_str", ["DELME", "file"])
def test_delete(dirs_dest, filter_str):
    # run the actual function to test

    for dir in dirs_dest:
        with patch("sys.argv", ["clifs", "del", str(dir), "--recursive"]), patch(
            "builtins.input", return_value="yes"
        ):
            main()
        print(f"Delete of {dir.name} went through.")

        assert not substr_in_dir_names(dir, sub_str=filter_str, files_only=True)
