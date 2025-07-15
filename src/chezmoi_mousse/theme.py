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

chezmoi_mousse_light = Theme(
    name="chezmoi-mousse-light",
    dark=False,
    foreground="#000000",
    primary="#006DC0",
    accent="#BF13CF",
    warning="#9D5B00",
    error="#a80014",
    success="#007324",
)

vars = chezmoi_mousse_dark.to_color_system().generate()
