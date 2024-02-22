"""Utilities for the command line interface"""

import argparse
from typing import Iterable, Optional, Union

from rich.console import Console, RenderableType
from rich.highlighter import Highlighter
from rich.progress import BarColumn, Progress, TaskProgressColumn, TimeRemainingColumn
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme

THEME_RICH = Theme(
    {
        "bar.complete": "default",
        "bar.finished": "green",
        "bar.back": "bright_black",
        "progress.percentage": "default",
        "progress.remaining": "bright_black",
        "rule.line": "default",
        "warning": "yellow",
        "error": "red",
        "folder": "yellow",
        "regex_match": "underline bright_cyan",
    },
)
CONSOLE = Console(theme=THEME_RICH, highlight=False)


class MatchHighlighter(Highlighter):  # pylint: disable=too-few-public-methods
    """Applies highlighting from a list of regular expressions."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.style = "regex_match"

    def highlight(self, text: Text) -> None:
        """Highlight :class:`rich.text.Text` at match location.

        Args:
            text (~Text): Text to highlighted.

        """
        text.highlight_regex(self.pattern, style=self.style)


def set_style(
    string: str,
    style: str = "red",
) -> str:
    """Set rich style for strings.

    :param string: String
    :param style: Style to set, defaults to "red"
    :return: String wrapped in style markup
    """
    if string.endswith("\\") and not string.endswith("\\\\"):
        string += "\\"
    return f"[{style}]{string}[/{style}]"


class LastActionProgress(Progress):
    """Progress showing the last action in a separate line."""

    def get_renderables(self) -> Iterable[RenderableType]:
        """Get a number of renderables for the progress display."""

        table = self.make_tasks_table(self.tasks)
        yield table
        for task in self.tasks:
            yield (
                f"{task.fields.get('last_action_desc','Last action')}: "
                f"{task.fields.get('last_action', '-')}"
            )


def size2str(size: float, color: str = "cyan") -> str:
    """Format data size in bites to nicely readable units.

    :param size: Input size in bites
    :param color: Output color for rich markup, defaults to "cyan"
    :return: String of data size wrapped in color markup
    """
    if size < 1024**2:
        unit = "KB"
        size = round(size / 1024, 2)
    elif size < 1024**3:
        unit = "MB"
        size = round(size / 1024**2, 2)
    elif size < 1024**4:
        unit = "GB"
        size = round(size / 1024**3, 2)
    elif size < 1024**5:
        unit = "TB"
        size = round(size / 1024**4, 2)
    else:
        unit = "PB"
        size = round(size / 1024**5, 2)
    return f"[{color}]{size:7.2f} {unit}[/{color}]"


def cli_bar(  # pylint: disable=too-many-arguments
    status: int,
    total: int,
    suffix: Union[str, Text] = "",
    print_out: bool = True,
    bar_len: int = 20,
    console: Optional[Console] = None,
) -> str:
    """Create progress bar and either print directly to console or return as string.

    :param status: Number of finished steps
    :param total: Total number of expected steps
    :param suffix: Suffix to add to the bar, defaults to ""
    :param print_out: Whether to print directly or not, defaults to True
    :param bar_len: Number of characters used for the bar, defaults to 20
    :param console: rich.console object to print to, defaults to None
    :return: Progress bar including percent indication and the suffix
    """
    filled_len = int(round(bar_len * status / float(total)))
    percents = round(100.0 * status / float(total), 1)
    proc_bar = "█" * filled_len + "-" * (bar_len - filled_len)
    bar_info = f"|{proc_bar}| {percents:5}%"
    if print_out:
        if console:
            console.print(bar_info, suffix)
        else:
            print(bar_info + " " + str(suffix))
    return bar_info + " " + str(suffix)


def user_query(message: str) -> bool:
    """Run user query.

    :param message: Message to show
    :return: Boolean indicating if the user input was "y" or "yes"
    """
    yes = {"yes", "y"}
    print(message)
    choice = input().lower()
    return choice in yes


def print_line(console: Console = CONSOLE, title: str = "") -> None:
    """Print a line to the console.

    :param console: rich.console to print to, defaults to CONSOLE
    :param title: Title included in the line, defaults to ""
    """
    console.print(Rule(title=title, align="center"))


def get_count_progress() -> Progress:
    """Get instance of a count progress.

    :return: progress
    """
    return Progress(
        "{task.description}",
        "{task.completed}",
    )


def get_last_action_progress() -> LastActionProgress:
    """Get instance of a progress bar displaying the last action in a separate line.

    :return: Progress
    """
    return LastActionProgress(
        "{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    )


class ClifsHelpFormatter(argparse.HelpFormatter):
    """Help text formatter for argparse.ArgumentParser

    Hides destination variables or positional args.
    Shows default values with string defaults being quoted."""

    # do not show dest variable for optional args in help
    def _get_default_metavar_for_optional(self, action: argparse.Action) -> str:
        return ""

    # show default values with quoted strings
    def _get_help_string(self, action: argparse.Action) -> str:
        action_help = action.help if action.help else ""
        if "%(default)" not in action_help and action.default is not argparse.SUPPRESS:
            defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                def_str = "%(default)s"
                if isinstance(action.default, str):
                    def_str = f"'{def_str}'"
                action_help += f" (default: {def_str})"
        return action_help
