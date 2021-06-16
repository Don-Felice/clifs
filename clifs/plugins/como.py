# -*- coding: utf-8 -*-


from clifs.clifs_plugin import ClifsPlugin
from clifs.utils_fs import como


def init_parser_como(parser):
    """
    Adding arguments to an argparse parser. Needed for all clifs_plugins.
    """
    parser.add_argument("dir_source", type=str,
                        help="Folder with files to copy/move from")
    parser.add_argument("dir_dest", type=str,
                        help="Folder to copy/move files to")
    parser.add_argument("-r", "--recursive", action='store_true',
                        help="Search recursively in source folder")
    parser.add_argument("-fl", "--filterlist", default=None,
                        help="Path to a file containing a list of files to copy/move (no header, sep.: \'\\n\')")
    parser.add_argument("-fs", "--filterstring", default=None,
                        help="Substring identifying files to be copied. not case sensitive.")
    parser.add_argument("-dr", "--dryrun", action='store_true',
                        help="Don't touch anything")


class Copy(ClifsPlugin):
    """
    Copy files
    """
    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        init_parser_como(parser)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        como(self.dir_source,
             self.dir_dest,
             move=False,
             recursive=self.recursive,
             path_filterlist=self.filterlist,
             filterstring=self.filterstring,
             dry_run=self.dryrun)


class Move(ClifsPlugin):
    """
    Move files
    """
    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs_plugins.
        """
        init_parser_como(parser)

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        como(self.dir_source,
             self.dir_dest,
             move=True,
             recursive=self.recursive,
             path_filterlist=self.filterlist,
             filterstring=self.filterstring,
             dry_run=self.dryrun)
