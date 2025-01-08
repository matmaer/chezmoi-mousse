"""The root chezmoi-mousse module."""

# from textual.widgets import RichLog

from chezmoi_mousse.commands import ChezmoiCommands
# from chezmoi_mousse.logger import MousseLogger

chezmoi = ChezmoiCommands()


# rlog = MousseLogger()

# class MousseLogger(RichLog):
#     def __init__(self):
#         super().__init__(
#             id="monlog",
#             highlight=True,
#             wrap=False,
#             markup=True,
#         )
#     def compose(self):
#         yield MousseLogger()
