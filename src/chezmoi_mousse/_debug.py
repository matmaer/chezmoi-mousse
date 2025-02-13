import os

from rich import inspect
from textual._log import LogGroup


class DebugUtils:

    @staticmethod
    def print_env_vars():
        for key, value in os.environ.items():
            print(f"{key}: {value}")

    # @staticmethod
    # def log_screen(screen: textual.screen.Screen):
    #     screen.log.debug(screen.__class__.__mro__)
    #     screen.log.debug(screen.ancestors)
    #     screen.log.debug(screen.children)
    #     screen.log.debug(screen.css_identifier)
    #     screen.log.debug(screen.css_tree)
    #     screen.log.debug(screen.tree)

    @staticmethod
    def inspect_object(some_object):
        return inspect(some_object, methods=True, help=True)

    @staticmethod
    def print_log_groups():
        return inspect(LogGroup, methods=True, help=True)
