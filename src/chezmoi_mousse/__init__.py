"""The root chezmoi-mousse module."""

from chezmoi_mousse.commands import ChezmoiCommands

chezmoi = ChezmoiCommands()

CM_CONFIG_DUMP = chezmoi.dump_config()
