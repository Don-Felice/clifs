# -*- coding: utf-8 -*-


from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_fs import rename_files


class FileRenamer(ClifsPlugin):
    """
    Regex-based file renaming.
    """

    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        parser.add_argument(
            "dir_source", type=str, help="Folder with files to rename from"
        )
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
            "-fs",
            "--filterstring",
            default=None,
            help="Substring identifying files to be renamed.",
        )
        parser.add_argument(
            "-r",
            "--recursive",
            action="store_true",
            help="Search recursively in source folder",
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

    def run(self):
        rename_files(
            self.dir_source,
            self.re_pattern,
            self.substitute,
            filterstring=self.filterstring,
            recursive=self.recursive,
            skip_preview=self.skip_preview,
        )
