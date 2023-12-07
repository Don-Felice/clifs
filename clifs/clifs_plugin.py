"""Definition of the ClifsPlugin interface"""


from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace

from clifs.utils_cli import CONSOLE


class ClifsPlugin(ABC):
    # Using ABC instead of typing.Protocol here as Protocols break resolving of
    # the __init__ method, see:
    # https://bugs.python.org/issue44807
    """
    Class to inherit for clifs plugins.
    """

    @staticmethod
    @abstractmethod
    def init_parser(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs plugins.
        """
        raise NotImplementedError

    def __init__(self, args: Namespace) -> None:
        """
        Converts arguments to instance attributes.
        """
        for arg in vars(args):
            setattr(self, arg, getattr(args, arg))
        self.console = CONSOLE

    @abstractmethod
    def run(self) -> None:
        """
        Running the plugin. Needed for all clifs plugins.
        """
        raise NotImplementedError
