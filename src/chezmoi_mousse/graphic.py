from textual.theme import Theme
# from textual.color import Gradient

CM_COLOR = {
    "success": "rgb(47, 166, 59)",
}

oled_deep_zen = Theme(
    name="oled-deep-zen", dark=True,
    primary="rgb(31, 110, 195)",
    # boost="",
    accent="rgb(195, 146, 255)",
    background="rgb(13, 17, 23)",
    foreground="rgb(219, 214, 199)",
    luminosity_spread=0.1,
    # panel="",
    secondary="rgb(36, 131, 123)",
    success=CM_COLOR["success"],
    text_alpha=0.9,
    warning="rgb(221, 175, 38)",
    error="rgb(176, 81, 55)",


    # old vars to integrate and for reference:
    # $ui_accent: rgb(98, 118, 147);
    # $ui_dark_accent: rgb(79, 95, 120);
    # $scrollbar_background: rgb(0, 4, 17);
    # $fade_start: rgb(67, 156, 251);
    # $fade_end: rgb(241, 135, 251);

    # vars to check:
    # "accent-muted"
    # "block-cursor-background"
    # "block-cursor-blurred-background"
    # "block-cursor-blurred-foreground"
    # "block-cursor-blurred-text-style"
    # "block-cursor-foreground"
    # "block-cursor-text-style"
    # "block-hover-background"
    # "border-blurred"
    # "border"
    # "button-color-foreground"
    # "button-focus-text-style"
    # "button-foreground"
    # "error-muted"
    # "footer-background"
    # "footer-description-background"
    # "footer-description-foreground"
    # "footer-foreground"
    # "footer-item-background"
    # "footer-key-background"
    # "footer-key-foreground"
    # "foreground-disabled"
    # "foreground-muted"
    # "input-cursor-background"
    # "input-cursor-foreground"
    # "input-cursor-text-style"
    # "input-selection-background"
    # "link-background-hover"
    # "link-background"
    # "link-color-hover"
    # "link-color"
    # "link-style-hover"
    # "link-style"
    # "primary-muted"
    # "scrollbar-active"
    # "scrollbar-background-active"
    # "scrollbar-background-hover"
    # "scrollbar-background"
    # "scrollbar-corner-color"
    # "scrollbar-hover"
    # "scrollbar"
    # "secondary-muted"
    # "success-muted"
    # "surface-active"
    # "text-accent"
    # "text-disabled"
    # "text-error"
    # "text-muted"
    # "text-primary"
    # "text-secondary"
    # "text-success"
    # "text-warning"
    # "text"
    # "warning-muted"
    # "markdown-h1-color"
    # "markdown-h1-background"
    # "markdown-h1-text-style"
    # "markdown-h2-color"
    # "markdown-h2-background"
    # "markdown-h2-text-style"
    # "markdown-h3-color"
    # "markdown-h3-background"
    # "markdown-h3-text-style"
    # "markdown-h4-color"
    # "markdown-h4-background"
    # "markdown-h4-text-style"
    # "markdown-h5-color"
    # "markdown-h5-background"
    # "markdown-h5-text-style"
    # "markdown-h6-color"
    # "markdown-h6-background"
    # "markdown-h6-text-style"
)


# TODO: use Gradient to construct FADE
FADE = (
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(102, 152, 251)",
    "rgb(137, 148, 251)",
    "rgb(171, 143, 251)",
    "rgb(206, 139, 251)",
    "rgb(241, 135, 251)",
    "rgb(206, 139, 251)",
    "rgb(171, 143, 251)",
    "rgb(137, 148, 251)",
    "rgb(102, 152, 251)",
)

SPLASH = """\
 _______ _______ _______ _______ ____ ____ _______ _o_
|       |   |   |    ___|___    |    ˇ    |       |   |
|    ===|       |     __'     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
"""