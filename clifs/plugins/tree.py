# -*- coding: utf-8 -*-


import os
import pathlib
from clifs.clifs_plugin import ClifsPlugin
from clifs.utils import wrap_string, ansiescape_colors

from colorama import init
init()      # allow for ansi escape sequences to have colorful cmd output

PIPE = "│"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "


class DirectoryTree(ClifsPlugin):
    """
    Display a tree of the file system including item sizes.
    """

    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all photoraspi_plugins.
        """
        parser.add_argument("root_dir", type=str, default=".", nargs='?',
                            help="Root directory to generate tree")
        parser.add_argument("-do", "--dirs_only", action='store_true', default=False,
                            help="Get info only on directories")

    def __init__(self, args):
        super().__init__(args)
        self.root_dir = pathlib.Path(self.root_dir)
        self._tree = []

    def run(self):
        self._add_directory(self.root_dir)
        for entry in self._tree:
            print(entry)

    @staticmethod
    def _size2str(size, ansiescape_color=ansiescape_colors['cyan']):
        if size >= (1024 * 1024 * 1024):
            unit = "GB"
            size = round(size / (1024 * 1024 * 1024), 2)
        else:
            unit = "MB"
            size = round(size / (1024 * 1024), 2)
        return wrap_string(f"size: {size} " + unit, prefix=ansiescape_color)

    def _add_directory(
            self, directory, index=0, entries_count=0, prefix="", connector="", ansiescape_color=ansiescape_colors['yellow']
            ):
        idx_dir = len(self._tree)   # get index of current directory in tree list to attach size info
        self._tree.append(f"{prefix}{connector}" + wrap_string(f"{directory.name}{os.sep}", prefix=ansiescape_color))

        if connector == "":     # for root dir
            pass
        elif index != entries_count - 1:
            prefix += PIPE_PREFIX
        else:                   # for last sub-dir
            prefix += SPACE_PREFIX

        entries = directory.iterdir()
        entries = sorted(entries, key=lambda item: not item.is_file())
        entries_count = len(entries)
        size = 0    # initialize size of sub-directories and files

        for index, entry in enumerate(entries):
            connector = ELBOW if index == entries_count - 1 else TEE
            if entry.is_dir():
                size += self._add_directory(entry, index, entries_count, prefix, connector)
            else:
                size += self._add_file(entry, prefix, connector)

        self._tree[idx_dir] = self._tree[idx_dir] + wrap_string(SPACE_PREFIX + self._size2str(size),
                                                                prefix=ansiescape_color)
        self._tree.append(prefix.rstrip())
        return size

    def _add_file(self, file, prefix, connector):
        size = file.stat().st_size
        if not self.dirs_only:
            self._tree.append(f"{prefix}{connector} {file.name}" + SPACE_PREFIX + self._size2str(size))
        return size
