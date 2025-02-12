from textual.theme import Theme

# from textual.color import Gradient


def rgb_to_hex(red, green, blue):
    return f"#{red:02x}{green:02x}{blue:02x}"


oled_deep_zen = Theme(
    name="oled-deep-zen",
    dark=True,
    luminosity_spread=0.9,
    text_alpha=0.9,
    accent="rgb(241, 135, 251)",  # fade end
    background="rgb(12, 14, 18)",
    error="rgb(203, 68, 31)",
    foreground="rgb(234, 232, 227)",
    panel="rgb(98, 118, 147)",
    primary="rgb(67, 156, 251)",  # fade end
    secondary="rgb(37, 146, 137)",
    success="rgb(63, 170, 77)",
    surface="rgb(24, 28, 34)",
    warning="rgb(224, 195, 30)",
    variables={
        "footer-background": "rgb(12, 14, 18)",
        "footer-item-background": "rgb(12, 14, 18)",
        "footer-key-background": "rgb(12, 14, 18)",
        "footer-description-background": "rgb(12, 14, 18)",
    },
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
    # "footer-description-foreground"
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
    "rgb(102, 152, 251)",
    "rgb(137, 148, 251)",
    "rgb(171, 143, 251)",
    "rgb(206, 139, 251)",
    "rgb(241, 135, 251)",
    "rgb(241, 135, 251)",
    "rgb(206, 139, 251)",
    "rgb(171, 143, 251)",
    "rgb(137, 148, 251)",
    "rgb(102, 152, 251)",
)


# provisional diagrams until dynamically created
FLOW_DIAGRAM = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │    chezmoi add    │                   │                   │
       │   chezmoi re-add  │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │   chezmoi apply   │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  chezmoi status   │                   │                   │
       │   chezmoi diff    │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │     git push      │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │           chezmoi git pull            │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │                   │    git commit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │    autoCommit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                autoPush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │   staging    │    │   git repo   │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""
