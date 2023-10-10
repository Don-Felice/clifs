"""
Main entry point
"""


import argparse
import sys
from importlib.metadata import entry_points

import colorama  # type: ignore

import clifs
from clifs.utils_cli import AnsiColor, wrap_string


def main() -> None:
    colorama.init()  # allow for ansi escape sequences to have colorful cmd output
    print(
        wrap_string(
            f"running `clifs` version: {clifs.__version__}", prefix=AnsiColor.GRAY
        )
    )

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    commands = parser.add_subparsers(title="Available plugins", dest="plugin")

    plugins = {}
    for entry_point in entry_points()["clifs.plugins"]:
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
