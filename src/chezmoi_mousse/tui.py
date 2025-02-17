from textual.app import App
from textual.theme import Theme

from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.loader import LoadingScreen
from chezmoi_mousse.operator import OperationTabs

__all__ = ["ChezmoiTUI"]


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
)


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        "loader": LoadingScreen,
    }

    def on_mount(self) -> None:
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        self.push_screen("loader")
