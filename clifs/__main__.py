"""Main entry point calling plugins"""

import argparse
import sys
from importlib.metadata import entry_points

import clifs
from clifs import ClifsPlugin
from clifs.utils_cli import CONSOLE, ClifsHelpFormatter


def main() -> None:
    """Main entry point calling plugins installed as 'clifs.plugins'"""
    parser = argparse.ArgumentParser(
        formatter_class=ClifsHelpFormatter,
        description="Multi-platform command line interface for file system operations.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="Show running 'clifs' version.",
    )

    commands = parser.add_subparsers(title="Available plugins", dest="plugin")

    plugins: dict[str, type[ClifsPlugin]] = {}
    plugin_entry_points = entry_points().select(group="clifs.plugins")

    for entry_point in plugin_entry_points:
        plugins[entry_point.name] = entry_point.load()
        subparser = commands.add_parser(
            entry_point.name,
            help=getattr(plugins[entry_point.name], "plugin_summary", None)
            or plugins[entry_point.name].__doc__,
            description=getattr(plugins[entry_point.name], "plugin_description", None)
            or getattr(plugins[entry_point.name], "plugin_summary", None)
            or plugins[entry_point.name].__doc__,
            formatter_class=ClifsHelpFormatter,
        )
        plugins[entry_point.name].init_parser(parser=subparser)

    if len(sys.argv) == 1:
        print("No function specified. Have a look at the awesome options:")
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    if args.version:
        CONSOLE.print(f"clifs {clifs.__version__}")
        if args.plugin is None:
            sys.exit(0)
    plugin = plugins[args.plugin](args)
    plugin.run()


if __name__ == "__main__":
    main()
