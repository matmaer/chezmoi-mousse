from textual.app import App, ComposeResult
from textual.widgets import Footer

# from chezmoi_mousse.greeter import LoadingWidget
from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from textual.theme import Theme

oled_deep_zen = Theme(
    name="oled-deep-zen", dark=True,

    foreground="#e0e4eb",
    background="#0d1117",
    primary="#439cfb",
    accent="#c392ff",
    secondary="#24837b",
    warning="#ad8301",
    error="#af3029",
    success="#66800b",

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


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        # "loading": LoadingWidget,
    }

    def compose(self) -> ComposeResult:
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        self.push_screen("inspect")
