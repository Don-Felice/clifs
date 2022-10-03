# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from pathlib import Path
from typing import List

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_fs import FileGetterMixin, como


def init_parser_como(parser: ArgumentParser):
    """
    Adding arguments to an argparse parser. Needed for all clifs_plugins.
    """
    parser.add_argument("dir_dest", type=Path, help="Folder to copy/move files to")
    parser.add_argument(
        "-se",
        "--skip_existing",
        action="store_true",
        help="Do nothing if file already exists in destination (instead of replacing).",
    )
    parser.add_argument(
        "-ka",
        "--keep_all",
        action="store_true",
        help="Keep both versions if a file already exists in destination "
        "(instead of replacing).",
    )
    parser.add_argument(
        "-flt",
        "--flatten",
        action="store_true",
        help="Flatten folder structure in output directory when running "
        "in recursive mode. "
        "Be careful with files of identical name in different subfolders as "
        "they will overwrite each other by default!",
    )
    parser.add_argument(
        "-dr", "--dryrun", action="store_true", help="Don't touch anything"
    )


class FileCopier(ClifsPlugin, FileGetterMixin):
    """
    Copy files
    """

    files2process: List[Path]
    dir_dest: Path
    skip_existing: bool
    keep_all: bool
    flatten: bool
    dryrun: bool

    @classmethod
    def init_parser(cls, parser: ArgumentParser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)
        init_parser_como(parser)

    def __init__(self, args):
        super().__init__(args)
        self.files2process = self.get_files2process(
            dir_source=self.dir_source,
            recursive=self.recursive,
            path_filterlist=self.filterlist,
            header_filterlist=self.filterlistheader,
            sep_filterlist=self.filterlistsep,
            filterstring=self.filterstring,
        )

    def run(self):
        self.exit_if_nothing_to_process(self.files2process)
        como(
            self.dir_source,
            self.dir_dest,
            files2process=self.files2process,
            move=False,
            skip_existing=self.skip_existing,
            keep_all=self.keep_all,
            flatten=self.flatten,
            dry_run=self.dryrun,
        )


class FileMover(ClifsPlugin, FileGetterMixin):
    """
    Move files
    """

    files2process: List[Path]
    dir_dest: Path
    skip_existing: bool
    keep_all: bool
    flatten: bool
    dryrun: bool

    @classmethod
    def init_parser(cls, parser: ArgumentParser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super().init_parser_mixin(parser)
        init_parser_como(parser)

    def __init__(self, args):
        super().__init__(args)
        self.files2process = self.get_files2process(
            dir_source=self.dir_source,
            recursive=self.recursive,
            path_filterlist=self.filterlist,
            header_filterlist=self.filterlistheader,
            sep_filterlist=self.filterlistsep,
            filterstring=self.filterstring,
        )

    def run(self):
        self.exit_if_nothing_to_process(self.files2process)
        como(
            self.dir_source,
            self.dir_dest,
            files2process=self.files2process,
            move=True,
            skip_existing=self.skip_existing,
            keep_all=self.keep_all,
            flatten=self.flatten,
            dry_run=self.dryrun,
        )
