"""
Main entry point
"""


import argparse
import sys
from importlib.metadata import entry_points
from typing import Dict, Type

import clifs
from clifs import ClifsPlugin
from clifs.utils_cli import CONSOLE, set_style


def main() -> None:
    CONSOLE.print(
        set_style(f"running `clifs` version: {clifs.__version__}", "bright_black")
    )

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    commands = parser.add_subparsers(title="Available plugins", dest="plugin")

    plugins: Dict[str, Type[ClifsPlugin]] = {}
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
