# -*- coding: utf-8 -*-


from clifs.utils_fs import FileGetterMixin
from tests.common.utils_testing import (
    parametrize_default_ids,
    dirs_source,
    dir_testrun,
    path_filterlist_txt,
    path_filterlist_csv,
    path_filterlist_tsv,
)


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
def test_file_getter(dirs_source, recursive, filter_str, path_filterlist, header_filterlist, sep_filterlist, request):

    for dir in dirs_source:
        # run the actual function to test
        file_getter = FileGetterMixin()

        files_found = file_getter.get_files2process(
            dir_source=dir,
            recursive=recursive,
            path_filterlist=path_filterlist if path_filterlist is None else request.getfixturevalue(path_filterlist),
            header_filterlist=header_filterlist,
            sep_filterlist=sep_filterlist,
            filterstring=filter_str,
        )

        pattern = f"*{filter_str}*" if filter_str else "*"

        if path_filterlist is None:
            if recursive:
                assert files_found == [
                    file for file in dir.rglob(pattern) if not file.is_dir()
                ]
            else:
                assert files_found == [
                    file for file in dir.glob(pattern) if not file.is_dir()
                ]
        
        else: 
            exp_files = ["L1_file_2.txt", "L2_file_1.txt", "L3_file_3.txt"]
            if recursive:
                assert files_found == [
                    file for file in dir.rglob(pattern) if not file.is_dir() and file.name in exp_files
                ]
            else:
                assert files_found == [
                    file for file in dir.glob(pattern) if not file.is_dir() and file.name in exp_files
                ]
