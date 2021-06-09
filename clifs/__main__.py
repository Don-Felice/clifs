# -*- coding: utf-8 -*-


import argparse
from pkg_resources import iter_entry_points
import sys


def main():

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(title='Available plugins', dest='plugin')

    plugins = {}
    for entry_point in iter_entry_points("clifs_plugins"):
        plugins[entry_point.name] = entry_point.load()
        subparser = commands.add_parser(entry_point.name, help=plugins[entry_point.name].__doc__)
        plugins[entry_point.name].init_parser(parser=subparser)

    if len(sys.argv) == 1:
        print("No function specified. Have a look at the awesome options:")
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    plugin = plugins[args.plugin](args)
    plugin.run()


if __name__ == "__main__":
    main()
