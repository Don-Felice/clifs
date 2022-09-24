# -*- coding: utf-8 -*-


from argparse import Namespace
from pathlib import Path
import shutil


import pytest

from clifs.plugins.rename import FileRenamer
from tests.common.utils_testing import (
    substr_in_dir_names,
    parametrize_default_ids,
    dir_testrun,
    dirs_source,
    dirs_source_ref,
    compare_files,
)


@parametrize_default_ids(
    ("re_pattern", "substitute"), [("file", "SUBSTITUTE"), (".txt", "123456")]
)
def test_delete(dirs_source, dirs_source_ref, re_pattern, substitute):
    # run the actual function to test

    for idx_dir, dir in enumerate(dirs_source):
        renamer = FileRenamer(
            Namespace(
                re_pattern=re_pattern,
                substitute=substitute,
                dir_source=dir,
                recursive=True,
                filterlist=None,
                filterlistheader=None,
                filterlistsep=None,
                filterstring=None,
                skip_preview=True,
            )
        )
        renamer.run()
        print(f"Renaming of {dir.name} went through.")

        assert not substr_in_dir_names(dir, sub_str=re_pattern, files_only=True)

        # revert and check conistency

        renamer = FileRenamer(
            Namespace(
                re_pattern=substitute,
                substitute=re_pattern,
                dir_source=dir,
                recursive=True,
                filterlist=None,
                filterlistheader=None,
                filterlistsep=None,
                filterstring=None,
                skip_preview=True,
            )
        )
        renamer.run()
        print(f"Re-renaming of {dir.name} went through.")

        assert not substr_in_dir_names(dir, sub_str=substitute, files_only=True)

        compare_files(dir_source=dirs_source_ref[idx_dir], dir_ref=dir)
