from textual.app import App
from textual.theme import Theme

from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.loader import LoadingScreen
from chezmoi_mousse.operator import OperationTabs


BACKGROUND = "rgb(12, 14, 18)"


oled_dark_zen = Theme(
    name="oled-dark-zen",
    dark=True,
    luminosity_spread=0.9,
    text_alpha=0.9,
    accent="rgb(241, 135, 251)",
    background=BACKGROUND,
    error="rgb(203, 68, 31)",
    foreground="rgb(234, 232, 227)",
    panel="rgb(98, 118, 147)",
    primary="rgb(67, 156, 251)",
    secondary="rgb(37, 146, 137)",
    success="rgb(63, 170, 77)",
    surface="rgb(24, 28, 34)",
    warning="rgb(224, 195, 30)",
    variables={
        # TODO: vars to consider
        # "accent-muted": ,
        # "primary-muted": ,
        # "secondary-muted": ,
        # "surface-active": ,
        # "text-primary": ,
        # "text-secondary": ,
        "footer-background": BACKGROUND,
        "footer-description-background": BACKGROUND,
        "footer-item-background": BACKGROUND,
        "footer-key-background": BACKGROUND,
        "link-background": BACKGROUND,
        "scrollbar-corner-color": BACKGROUND,
    },
)


class ChezmoiTUI(App):

    BINDINGS = [
        ("l, L", "app.push_screen('loader')", "loader"),
    ]

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        "loader": LoadingScreen,
    }

    def loading_completed(self) -> None:
        self.push_screen("inspector")

    def on_mount(self) -> None:
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loader", callback=self.loading_completed)
