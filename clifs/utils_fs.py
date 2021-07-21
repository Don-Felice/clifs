# -*- coding: utf-8 -*-


from pathlib import Path
import re
import shutil
import sys

from clifs.utils_cli import wrap_string, cli_bar, user_query, ANSI_COLORS


def _find_bad_char(string):
    """Check stings for characters causing problems in windows file system."""
    bad_chars = r"~“#%&*:<>?/\{|}"
    return [x for x in bad_chars if x in string]


def _get_files_by_filterstring(dir_source, filterstring=None, recursive=False):
    pattern_search = "*" + filterstring + "*" if filterstring else "*"
    if recursive:
        pattern_search = "**/" + pattern_search
    return [file for file in dir_source.glob(pattern_search) if not file.is_dir()]


def _get_path_dest(path_src, path_file, path_out, flatten=False):
    if flatten:
        return path_out / path_file.name
    else:
        return Path(str(path_file).replace(str(path_src), str(path_out)))


def _filter_by_list(files, path_list):
    list_filter = open(path_list).read().splitlines()
    return [i for i in files if i.name in list_filter]


def _get_unique_path(path_candidate, paths_taken):
    name_file = path_candidate.stem
    if path_candidate in paths_taken:
        count_match = re.match(r".* \((\d)\)$", name_file)
        if count_match:
            count = int(count_match.group(1)) + 1
            name_file_new = " ".join(name_file.split(" ")[0:-1]) + f" ({count})"
        else:
            name_file_new = name_file + " (2)"
        path_new = path_candidate.parent / (name_file_new + path_candidate.suffix)
        return _get_unique_path(path_new, paths_taken)
    else:
        return path_candidate


def _print_rename_message(
    message, num_file, num_files_all, preview_mode=False, space_prefix="    "
):
    if preview_mode:
        print(space_prefix + message)
    else:
        cli_bar(num_file, num_files_all, suffix=space_prefix + message)


def como(
    dir_source,
    dir_dest,
    *,
    move=False,
    recursive=False,
    path_filterlist=None,
    filterstring=None,
    skip_existing=False,
    keep_all=False,
    flatten=False,
    dry_run=False,
):
    """
    COpy or MOve files

    :param skip_existing:
    :param keep_all:
    :param flatten:
    :param dir_source:
    :param dir_dest:
    :param move:
    :param recursive:
    :param path_filterlist:
    :param filterstring:
    :param dry_run:
    """
    assert not (skip_existing and keep_all), (
        "You can only choose to either skip existing files "
        "or keep both versions. Choose wisely!"
    )

    dir_source = Path(dir_source)
    dir_dest = Path(dir_dest)

    dir_dest.parent.mkdir(exist_ok=True, parents=True)

    files2process = _get_files_by_filterstring(
        dir_source, filterstring=filterstring, recursive=recursive
    )

    if path_filterlist:
        files2process = _filter_by_list(files2process, path_filterlist)

    # get existing files
    if skip_existing or keep_all:
        files_present = [file for file in dir_dest.rglob("*") if not file.is_dir()]
    elif flatten:
        files_present = []

    str_process = "moving" if move else "copying"
    print(
        f"Will start {str_process} {len(files2process)} files from:"
        f"\n{dir_source}"
        f"\nto"
        f"\n{dir_dest}"
    )
    print("-----------------------------------------------------")

    if files2process:
        num_files2process = len(files2process)
        for num_file, file in enumerate(files2process, 1):
            txt_report = f"Last: {file.name}"
            filepath_dest = _get_path_dest(dir_source, file, dir_dest, flatten=flatten)
            if skip_existing and filepath_dest in files_present:
                txt_report = wrap_string(
                    f"Skipped as already present:{file.name}", ANSI_COLORS["yellow"]
                )
                cli_bar(
                    num_file,
                    num_files2process,
                    suffix="of files processed. " + txt_report,
                )
                continue
            elif keep_all:
                filepath_dest_new = _get_unique_path(filepath_dest, files_present)
                if not filepath_dest_new == filepath_dest:
                    txt_report = wrap_string(
                        f"Changed name as already present: "
                        f"{filepath_dest.name} -> {filepath_dest_new.name}",
                        ANSI_COLORS["yellow"],
                    )
                    filepath_dest = filepath_dest_new
            if not dry_run:
                if not flatten:
                    filepath_dest.parent.mkdir(exist_ok=True, parents=True)
                if move:
                    shutil.move(str(file), str(filepath_dest))
                else:
                    shutil.copy2(str(file), str(filepath_dest))
            cli_bar(
                num_file, num_files2process, suffix=" of files processed. " + txt_report
            )

        str_process = "moved" if move else "copied"
        print(f"Hurray, {num_file} files have been {str_process}.")
    else:
        print("No files to process.")


def rename_files(
    dir_source,
    re_pattern,
    replacement,
    *,
    filterstring=None,
    recursive=False,
    skip_preview=False,
):

    dir_source = Path(dir_source)
    files_present = [file for file in dir_source.rglob("*") if not file.is_dir()]
    files2process = _get_files_by_filterstring(
        dir_source, filterstring=filterstring, recursive=recursive
    )

    if files2process:
        if not skip_preview:
            _rename_files(
                files2process,
                re_pattern,
                replacement,
                files_present=files_present,
                preview_mode=True,
            )
            if not user_query(
                'If you want to apply renaming, give me a "yes" or "y" now!'
            ):
                print("Will not rename for now. See you soon.")
                sys.exit(0)

        num_files_proc, num_files_ren = _rename_files(
            files2process,
            re_pattern,
            replacement,
            files_present=files_present,
            preview_mode=False,
        )
        print(
            f"Hurray, {num_files_proc} files have been processed, "
            f"{num_files_ren} have been renamed."
        )
    else:
        print("No files to process.")


def _rename_files(
    files2process, re_pattern, replacement, *, files_present, preview_mode=True
):
    num_files2process = len(files2process)
    print(f"Renaming {num_files2process} files.")
    if preview_mode:
        print("Preview:")
        files_present = files_present.copy()

    num_bad_results = 0
    num_name_conflicts = 0
    num_files_renamed = 0
    for num_file, path_file in enumerate(files2process, 1):
        name_old = path_file.name
        name_new = re.sub(re_pattern, replacement, name_old)
        message_rename = f"{name_old:35} -> {name_new:35}"

        # skip files that are not renamed
        if name_new == name_old:
            message_rename = wrap_string(message_rename, ANSI_COLORS["gray"])
            _print_rename_message(
                message_rename, num_file, num_files2process, preview_mode=preview_mode
            )
            continue

        # skip files if renaming would result in bad characters
        found_bad_chars = _find_bad_char(name_new)
        if found_bad_chars:
            str_bad_chars = ",".join(found_bad_chars)
            message_rename += wrap_string(
                "    Warning: not doing renaming as it would result "
                f'in bad characters "{str_bad_chars}" '
            )
            num_bad_results += 1
            _print_rename_message(
                message_rename, num_file, num_files2process, preview_mode=preview_mode
            )
            continue

        # make sure resulting paths are unique
        path_file_new = path_file.parent / name_new
        files_present.remove(path_file)
        path_file_unique = _get_unique_path(path_file_new, files_present)
        files_present.append(path_file_unique)
        if not path_file_new == path_file_unique:
            path_file_new = path_file_unique
            name_new = path_file_unique.name
            message_rename = f"{name_old:35} -> {name_new:35}"
            message_rename += wrap_string(
                "    Warning: resulting name would already be present in folder. "
                "Will add numbering suffix.",
                ANSI_COLORS["yellow"],
            )
            num_name_conflicts += 1

        _print_rename_message(
            message_rename, num_file, num_files2process, preview_mode=preview_mode
        )
        if not preview_mode and not name_old == name_new:
            path_file.rename(path_file_new)
            num_files_renamed += 1

    if num_bad_results:
        print(
            wrap_string(
                f"Warning: {num_bad_results} out of {num_files2process} "
                f"files not renamed as it would result in bad characters."
            )
        )
    if num_name_conflicts:
        print(
            wrap_string(
                f"Warning: {num_name_conflicts} out of {num_files2process} "
                f"renamings would have resulted in name conflicts. "
                f"Added numbering suffices to get unique names."
            )
        )
    return num_file, num_files_renamed
