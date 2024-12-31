""" The root chezmoi-mousse module."""

__version__ = "0.1.0"

from chezmoi_mousse.common import ChezmoiContext

CHEZMOI_CONFIG = ChezmoiContext().get_config()
CHEZMOI_DATA = ChezmoiContext().get_data()

CHEZMOI_MANAGED = ChezmoiContext().get_chezmoi_managed()
