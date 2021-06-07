# -*- coding: utf-8 -*-


from pathlib import Path
import shutil
from clifs.clifs_plugin import ClifsPlugin
from clifs.utils import wrap_string, ansiescape_colors, size2str


from colorama import init
init()      # allow for ansi escape sequences to have colorful cmd output


class DiscUsageExplorer(ClifsPlugin):
    """
    Display a tree of the file system including item sizes.
    """

    @staticmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all photoraspi_plugins.
        """
        parser.add_argument("dirs", type=str, default=".", nargs='+',
                            help="Directories do get info from.")

    def __init__(self, args):
        super().__init__(args)
        self._dict_usage = self._get_usage_info()

    def run(self):
        self._print_usage_info()
        pass

    def _get_usage_info(self):
        disc_usage = {}
        for directory in self.dirs:
            dict_usage = {}
            dict_usage['total'], dict_usage['used'], dict_usage['free'] = shutil.disk_usage(directory)
            disc_usage[directory] = dict_usage
        return disc_usage

    def _print_usage_info(self):
        print("")
        for directory, dict_usage in self._dict_usage.items():
            name_dir = Path(directory).name if not Path(directory).name == "" else directory
            print(name_dir + "    " + wrap_string("(" + directory + ")", prefix=ansiescape_colors['gray']))
            if dict_usage['used'] / dict_usage['total'] > 0.9:
                color = ansiescape_colors['red']
            elif dict_usage['used'] / dict_usage['total'] > 0.70:
                color = ansiescape_colors['yellow']
            else:
                color = ansiescape_colors['default']

            str_total = size2str(dict_usage['total'],
                                 ansiescape_color=ansiescape_colors['default'])
            str_used = size2str(dict_usage['used'],
                                ansiescape_color=ansiescape_colors['default'])
            str_free = size2str(dict_usage['free'],
                                ansiescape_color=color)

            print(f"└── total: {str_total}    "
                  f"used: {str_used}    "
                  f"free: {str_free}")
