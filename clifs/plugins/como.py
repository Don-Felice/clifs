# -*- coding: utf-8 -*-

from pathlib import Path

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_fs import FileGetterMixin, como


def init_parser_como(parser):
    """
    Adding arguments to an argparse parser. Needed for all clifs_plugins.
    """
    parser.add_argument("dir_dest", type=str, help="Folder to copy/move files to")
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
        "they will overwrite each other!",
    )
    parser.add_argument(
        "-dr", "--dryrun", action="store_true", help="Don't touch anything"
    )


class FileCopier(ClifsPlugin, FileGetterMixin):
    """
    Copy files
    """

    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super(FileCopier, FileCopier).init_parser_mixin(parser)
        init_parser_como(parser)

    def __init__(self, args):
        super().__init__(args)
        self.dir_source = Path(self.dir_source)
        self.dir_dest = Path(self.dir_dest)
        self.files2process = self.get_files2process(
            dir_source=self.dir_source,
            recursive=self.recursive,
            path_filterlist=self.filterlist,
            header_filterlist=self.filterlistheader,
            sep_filterlist=self.filterlistsep,
            filterstring=self.filterstring,
        )

    def run(self):
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


class FileMover(ClifsPlugin):
    """
    Move files
    """

    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super(FileCopier, FileCopier).init_parser_mixin(parser)
        init_parser_como(parser)

    def __init__(self, args):
        super().__init__(args)
        self.dir_source = Path(self.dir_source)
        self.dir_dest = Path(self.dir_dest)
        self.files2process = self.get_files2process(
            dir_source=self.dir_source,
            recursive=self.recursive,
            path_filterlist=self.filterlist,
            header_filterlist=self.filterlistheader,
            sep_filterlist=self.filterlistsep,
            filterstring=self.filterstring,
        )

    def run(self):
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
