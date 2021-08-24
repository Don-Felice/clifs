# -*- coding: utf-8 -*-

from pathlib import Path

from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_fs import FileGetterMixin, rename_files


class FileRenamer(ClifsPlugin, FileGetterMixin):
    """
    Regex-based file renaming.
    """

    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        # add args from FileGetterMixin to arg parser
        super(FileRenamer, FileRenamer).init_parser_mixin(parser)

        parser.add_argument(
            "-re",
            "--re_pattern",
            default=".*",
            help="Pattern identifying the substring to be replaced. "
            "Supports syntax from regex module "
            "(https://docs.python.org/3/library/re.html).",
        )
        parser.add_argument(
            "-s",
            "--substitute",
            default="",
            help="String to use as replacement. "
            "You can use \\1 \\2 etc. to refer to matching groups. "
            "A pattern like '(.+)\\.(.+)' in combination "
            "with a replacement like '\\1_suffix.\\2' will append suffixes. "
            "Defaults to empty string",
        )
        parser.add_argument(
            "-sp",
            "--skip_preview",
            action="store_true",
            help="Skip preview on what would happen and directly rename. "
            "Only for the brave...",
        )

    def __init__(self, args):
        super().__init__(args)
        self.dir_source = Path(self.dir_source)
        self.files2process = self.get_files2process(
            dir_source=self.dir_source,
            recursive=self.recursive,
            path_filterlist=self.filterlist,
            header_filterlist=self.filterlistheader,
            sep_filterlist=self.filterlistsep,
            filterstring=self.filterstring,
        )

    def run(self):
        rename_files(
            self.files2process,
            self.re_pattern,
            self.substitute,
            skip_preview=self.skip_preview,
        )
