# -*- coding: utf-8 -*-


import shutil
from pathlib import Path

from clifs.utils_cli import cli_bar


def como(dir_source, dir_dest, move=False, recursive=False, path_filterlist=None, filterstring=None, dry_run=False):
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

    if filterstring:
        pattern_search = '*' + filterstring + '*'
    else:
        pattern_search = '*'

    if recursive:
        files = (file for file in dir_source.rglob(pattern_search) if not file.is_dir())
    else:
        files = (file for file in dir_source.glob(pattern_search) if not file.is_dir())

    if path_filterlist:
        list2copy = open(path_filterlist).read().splitlines()
        files2copy = [i for i in files if i.name in list2copy]
    else:
        files2copy = list(files)

    if move:
        print('Moving files from:\n', dir_source, "\n to \n", dir_dest)
    else:
        print('Copying files from:\n', dir_source, "\n to \n", dir_dest)
    print('-----------------------------------------------------')

    num_file = 0
    for file in files2copy:
        if move:
            print('moving: ' + file.name)
            if not dry_run:
                shutil.move(str(file), str(dir_dest / file.name))
        else:
            print('copying: ' + file.name)
            if not dry_run:
                shutil.copy2(str(file), str(dir_dest / file.name))
        num_file += 1
        cli_bar(num_file, len(files2copy), suffix='of files copied')

    print(f"Hurray, {num_file} files have been copied/moved.")
