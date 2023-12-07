"""Utilities for the command line interface"""

from enum import Enum
from typing import Iterable, Optional

from rich.console import Console, RenderableType
from rich.progress import BarColumn, Progress, TaskProgressColumn, TimeRemainingColumn
from rich.rule import Rule
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
    },
)
CONSOLE = Console(theme=THEME_RICH, highlight=False)


class AnsiColor(str, Enum):
    """Ansi escape colors."""

    DEFAULT = "\033[0m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    GRAY = "\033[0;90m"
    GREEN = "\033[0;32m"
    MAGENTA = "\033[0;35m"
    RED = "\033[0;31m"
    WHITE = "\033[0;37m"
    YELLOW = "\033[0;93m"

    def __str__(self) -> str:
        return self.value


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
    suffix: str = "",
    print_out: bool = True,
    bar_len: int = 20,
    console: Optional[Console] = None,
) -> str:
    """Create progress bar ans either print directly to console or return as string.

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
    res_bar = "█" * filled_len + "-" * (bar_len - filled_len)
    output = f"|{res_bar}| {percents:5}% {suffix}"
    if print_out:
        if console:
            console.print(output)
        else:
            print(output)
    return output


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
    console.print(Rule(title=title, align="left"))


def get_count_progress() -> Progress:
    """Get instance of a count progress.

    :return: progress
    """
    return Progress(
        "{task.description}",
        "{task.completed}",
    )


def get_last_action_progress() -> LastActionProgress:
    """Get instance of  a progress bar indicating the last action in a separate line.

    :return: Progress
    """
    return LastActionProgress(
        "{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    )
