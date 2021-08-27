# -*- coding: utf-8 -*-


import argparse
import colorama  # type: ignore
from pkg_resources import iter_entry_points  # type: ignore
import sys


def main():
    colorama.init()  # allow for ansi escape sequences to have colorful cmd output

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    commands = parser.add_subparsers(title="Available plugins", dest="plugin")

    plugins = {}
    for entry_point in iter_entry_points("clifs_plugins"):
        plugins[entry_point.name] = entry_point.load()
        subparser = commands.add_parser(
            entry_point.name, help=plugins[entry_point.name].__doc__
        )
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
