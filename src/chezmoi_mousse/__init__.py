""" The root chezmoi-mousse module."""

from chezmoi_mousse.operate import ChezmoiCommands

CM_CONFIG_DUMP = ChezmoiCommands().dump_config()
CM_DATA = ChezmoiCommands().data()
CM_DOCTOR = ChezmoiCommands().doctor()
CM_CONFIG_CAT = ChezmoiCommands().cat_config()
