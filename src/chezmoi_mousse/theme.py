"""Convenience module to access derived colors managed by the textual
ColorSystem.

Var names accessible from the the vars dict. Updated on theme change by gui.py.
"""

from textual.theme import Theme

chezmoi_mousse_dark = Theme(
    name="chezmoi-mousse-dark",
    dark=True,
    accent="#F187FB",
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DEDAE1",
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    surface="#101010",  # see also textual/theme.py
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)


vars = chezmoi_mousse_dark.to_color_system().generate()
