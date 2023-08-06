"""
Definition of the ClifsPlugin interface
"""


from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace


class ClifsPlugin(ABC):
    """
    Class to inherit for clifs plugins.
    """

    @staticmethod
    @abstractmethod
    def init_parser(parser: ArgumentParser) -> None:
        """
        Adding arguments to an argparse parser. Needed for all clifs plugins.
        """
        raise NotImplementedError()

    @abstractmethod
    def __init__(self, args: Namespace) -> None:
        """
        Converts arguments to instance attributes.
        """
        for arg in vars(args):
            setattr(self, arg, getattr(args, arg))

    @abstractmethod
    def run(self):
        """
        Running the plugin. Needed for all clifs plugins.
        """
        raise NotImplementedError()
