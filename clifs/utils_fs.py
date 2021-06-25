# -*- coding: utf-8 -*-


from pathlib import Path
import re
import shutil
import sys

from clifs.utils_cli import wrap_string, cli_bar


def _find_bad_char(string):
    """Check stings for characters causing problems in windows file system."""
    bad_chars = r'~“#%&*:<>?/\{|}'
    return [x for x in bad_chars if x in string]


def _get_files_by_filterstring(dir_source, filterstring=None, recursive=False):
    pattern_search = '*' + filterstring + '*' if filterstring else '*'
    if recursive:
        pattern_search = '**/' + pattern_search
    return [file for file in dir_source.glob(pattern_search) if not file.is_dir()]


def _get_path_dest(path_src, path_file, path_out, flatten=False):
    if flatten:
        return path_out / path_file.name
    else:
        return Path(str(path_file).replace(str(path_src), str(path_out)))


def _filter_by_list(files, path_list):
    list_filter = open(path_list).read().splitlines()
    return [i for i in files if i.name in list_filter]


def _user_query(message):
    yes = {'yes', 'y'}
    print(message)
    choice = input().lower()
    if choice in yes:
        return True
    else:
        return False


def como(dir_source, dir_dest, move=False, recursive=False,
         path_filterlist=None, filterstring=None, flatten=False, dry_run=False):
    """
    COpy or MOve files

    :param dir_source:
    :param dir_dest:
    :param move:
    :param recursive:
    :param path_filterlist:
    :param filterstring:
    :param dry_run:
    """
    dir_source = Path(dir_source)
    dir_dest = Path(dir_dest)

    dir_dest.parent.mkdir(exist_ok=True, parents=True)

    files2process = _get_files_by_filterstring(dir_source, filterstring=filterstring, recursive=recursive)

    if path_filterlist:
        files2process = _filter_by_list(files2process, path_filterlist)

    str_process = 'moving' if move else 'copying'
    print(f'Will start {str_process} {len(files2process)} files from:\n{dir_source}\nto\n{dir_dest}')
    print('-----------------------------------------------------')

    if files2process:
        num_files2process = len(files2process)
        for num_file, file in enumerate(files2process, 1):
            print(f'{str_process}: {file.name}')
            if not dry_run:
                filepath_dest = _get_path_dest(dir_source, file, dir_dest, flatten=flatten)
                if not flatten:
                    filepath_dest.parent.mkdir(exist_ok=True, parents=True)
                if move:
                    shutil.move(str(file), str(filepath_dest))
                else:
                    shutil.copy2(str(file), str(filepath_dest))
            cli_bar(num_file, num_files2process, suffix='of files processed')

        str_process = 'moved' if move else 'copied'
        print(f"Hurray, {num_file} files have been {str_process}.")
    else:
        print('No files to process.')


def rename_files(dir_source, re_pattern, replacement,
                 filterstring=None, recursive=False, skip_preview=False):

    dir_source = Path(dir_source)
    files2process = _get_files_by_filterstring(dir_source, filterstring=filterstring, recursive=recursive)

    if files2process:
        if not skip_preview:
            _rename_files(files2process, re_pattern, replacement, preview_only=True)
            if not _user_query("If you want to apply renaming, give me a \"yes\" or \"y\" now!"):
                print("Will not rename for now. See you soon.")
                sys.exit(0)

        num_file = _rename_files(files2process, re_pattern, replacement, preview_only=False)
        print(f"Hurray, {num_file} files have been processed.")
    else:
        print('No files to process.')


def _rename_files(files2process, re_pattern, replacement, preview_only=True):
    num_files2process = len(files2process)
    print(f'Renaming {num_files2process} files.')
    if preview_only:
        print("Preview:")

    num_bad_results = 0
    for num_file, file in enumerate(files2process, 1):
        name_old = file.name
        name_new = re.sub(re_pattern, replacement, name_old)
        message_rename = f"{name_old:35} -> {name_new:35}"

        found_bad_chars = _find_bad_char(name_new)
        if found_bad_chars:
            str_bad_chars = ",".join(found_bad_chars)
            message_rename += wrap_string("    Warning: not doing renaming as it would result "
                                          f"in bad characters \"{str_bad_chars}\" ")
            num_bad_results += 1

        if preview_only:
            print("    " + message_rename)
        else:
            path_new = file.parent / name_new
            cli_bar(num_file, num_files2process, suffix=f'    {message_rename}')
            if not found_bad_chars:
                file.rename(path_new)

    if num_bad_results:
        print(wrap_string(f"Warning: {num_bad_results} out of {num_files2process} "
                          f"files not renamed as it would result in bad characters."))
    return num_file
