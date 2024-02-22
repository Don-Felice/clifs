import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from clifs.__main__ import main
from clifs.plugins.edit import StreamingEditor
from tests.common.utils_testing import parametrize_default_ids


def test_parse_line_numbers():
    sed_mock = Mock()

    # single digit
    sed_mock.lines = "7"
    assert StreamingEditor.parse_line_nums(sed_mock) == [7]
    # list
    sed_mock.lines = "4,2,9,11,333333"
    assert StreamingEditor.parse_line_nums(sed_mock) == [4, 2, 9, 11, 333333]
    # range
    sed_mock.lines = "1-4242"
    assert StreamingEditor.parse_line_nums(sed_mock) == range(1, 4243)

    # zero included list
    sed_mock.lines = "0,4,2,9,11,333333"
    with pytest.raises(SystemExit) as e:
        StreamingEditor.parse_line_nums(sed_mock)
    assert e.type == SystemExit
    assert e.value.code == 1

    # zero included range
    sed_mock.lines = "0-111"
    with pytest.raises(SystemExit) as e:
        StreamingEditor.parse_line_nums(sed_mock)
    assert e.type == SystemExit
    assert e.value.code == 1

    # negatives included
    sed_mock.lines = "-5,10"
    with pytest.raises(SystemExit) as e:
        StreamingEditor.parse_line_nums(sed_mock)
    assert e.type == SystemExit
    assert e.value.code == 1

    # improper formatting
    sed_mock.lines = "2-10-13"
    with pytest.raises(SystemExit) as e:
        StreamingEditor.parse_line_nums(sed_mock)
    assert e.type == SystemExit
    assert e.value.code == 1


@parametrize_default_ids(
    ("pattern", "replacement"),
    [("next", "other"), (r"^.*$", "blub")],
)
@parametrize_default_ids("line_nums", [None, [1], [2, 3], [5], range(1, 2)])
def test_replace(pattern, replacement, line_nums):
    sed_mock = MagicMock(
        encoding="utf-8", line_nums=line_nums, pattern=pattern, replacement=replacement
    )

    file_content = [
        "l1 some example line\n",
        "l2 some next example line\n",
        "l3 some next next example line\n",
    ]

    with patch(
        "pathlib.Path.open",
        unittest.mock.mock_open(read_data="".join(file_content)),
    ) as m:
        StreamingEditor.replace(sed_mock, Path("some_file.txt"))

    # check files are properly accessed
    assert m.mock_calls.count(call("r", encoding="utf-8")) == 1
    assert m.mock_calls.count(call("w", encoding="utf-8")) == 1

    # check lines are properly modified and written
    line_nums = range(1, len(file_content) + 1) if line_nums is None else line_nums
    exp_calls = []
    for i, line in enumerate(file_content, 1):
        if i in line_nums:
            exp_calls.append(call(re.sub(pattern, replacement, line)))
        else:
            exp_calls.append(call(line))
    handle = m()
    handle.write.assert_has_calls(exp_calls)


@parametrize_default_ids(
    ("pattern", "replacement"),
    [("next", "other"), (r"^.*$", "blub")],
)
@parametrize_default_ids("line_nums", [None, [1], [2, 3], [5], range(1, 2)])
@parametrize_default_ids("max_previews", [0, 2, 1000])
def test_preview_replace(capsys, pattern, replacement, line_nums, max_previews):
    file_content = [
        "l1 some example line\n",
        "l2 some next example line\n",
        "l3 some next next example line\n",
    ]

    mock_args = MagicMock(
        encoding="utf-8",
        pattern=pattern,
        replacement=replacement,
        max_previews=max_previews,
    )

    with patch(
        "pathlib.Path.open",
        unittest.mock.mock_open(read_data="".join(file_content)),
    ) as m, patch.object(
        StreamingEditor, "get_paths", return_value=["bla", "blub"]
    ), patch.object(StreamingEditor, "parse_line_nums", return_value=line_nums):
        sed = StreamingEditor(mock_args)
        StreamingEditor.preview_replace(sed, Path("some_file.txt"))

    # check files are properly accessed
    assert m.mock_calls.count(call("r", encoding="utf-8")) == 1  # we read
    assert m.mock_calls.count(call("w", encoding="utf-8")) == 0  # we do not write

    captured = capsys.readouterr()
    print(f"{captured.out=}")

    # check lines are properly modified and written
    line_nums = range(1, len(file_content) + 1) if line_nums is None else line_nums
    count_changes = 0
    for i, line in enumerate(file_content, 1):
        mod_line = re.sub(pattern, replacement, line)

        if i in line_nums and line != mod_line and count_changes < max_previews:
            assert f"  l{i} old: {line}" in captured.out
            assert f"  l{i} new: {mod_line}" in captured.out
            count_changes += 1
        else:
            assert f"  l{i} old: {line}" not in captured.out
            assert (
                f"  l{i} new: {re.sub(pattern, replacement, line)}" not in captured.out
            )


@parametrize_default_ids(
    ("pattern", "replacement"),
    [("Lore", "ipsum"), ("\\n", "-")],
)
@parametrize_default_ids("dont_overwrite", [False, True])
@parametrize_default_ids("max_previews", [0, 5, 1000])
def test_streaming_editor(
    dirs_source, pattern, replacement, dont_overwrite, max_previews
):
    # run the actual function to test

    file_contents_initial = {}
    for file in dirs_source[0].rglob("*"):
        if file.is_file():
            with file.open("r") as f:
                file_contents_initial[file.name] = f.read()

    patch_args = [
        "clifs",
        "sed",
        str(dirs_source[0]),
        "--pattern",
        pattern,
        "--replacement",
        replacement,
        "--max_previews",
        str(max_previews),
        "--recursive",
    ]
    if dont_overwrite:
        patch_args.append("--dont_overwrite")

    with patch("sys.argv", patch_args), patch("builtins.input", return_value="yes"):
        main()

    print("Editing went through.")

    files_after_editing = [f.name for f in dirs_source[0].rglob("*") if f.is_file()]
    # check that no files got lost
    for file in file_contents_initial.keys():
        assert file in files_after_editing

    if dont_overwrite:
        for file in dirs_source[0].rglob("*"):
            if file.is_file():
                if "_edited" in file.stem:
                    # check edited files are modified
                    with file.open("r") as f:
                        file_content_modified = f.read()
                    assert file_content_modified == re.sub(
                        pattern,
                        replacement,
                        file_contents_initial[file.name.replace("_edited", "")],
                    )
                else:
                    # check initial files are untouched
                    with file.open("r") as f:
                        file_content_modified = f.read()
                    assert file_content_modified == file_contents_initial[file.name]

    else:
        for file in dirs_source[0].rglob("*"):
            if file.is_file():
                # check that temp files are renamed to original file name
                assert "_edited" not in file.stem
                with file.open("r") as f:
                    file_content_modified = f.read()
                assert file_content_modified == re.sub(
                    pattern, replacement, file_contents_initial[file.name]
                )
