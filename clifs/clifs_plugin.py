# -*- coding: utf-8 -*-


# external imports
from abc import ABC, abstractmethod


class ClifsPlugin(ABC):
    """
    Class to inherit for clifs plugins.
    """

    @staticmethod
    @abstractmethod
    def init_parser(parser):
        """
        Adding arguments to an argparse parser. Needed for all clifs plugins.
        """
        raise NotImplementedError()

    @abstractmethod
    def __init__(self, args):
        """
        Converts arguments to class attributes.
        """
        for arg in vars(args):
            setattr(self, arg, getattr(args, arg))

    @abstractmethod
    def run(self):
        """
        Running the plugin. Needed for all clifs plugins.
        """
        raise NotImplementedError()
