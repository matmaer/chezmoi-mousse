""" The root chezmoi-mousse module."""

__version__ = "0.1.0"

from chezmoi_mousse.common import ChezmoiCommands

CM_CONFIG_DUMP = ChezmoiCommands().dump_config()
CM_DATA = ChezmoiCommands().data()
CM_DOCTOR = ChezmoiCommands().doctor()
CM_CONFIG_CAT = ChezmoiCommands().cat_config()
