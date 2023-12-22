"""Test the path getter mixin class"""


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
