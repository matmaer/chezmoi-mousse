from textual.app import App, ComposeResult

from textual.theme import Theme
from textual.widgets import Footer, Header, Pretty, Static, TabbedContent

from chezmoi_mousse.loader import LoadingScreen
from chezmoi_mousse.commands import chezmoi
from chezmoi_mousse.operator import ChezmoiDoctor, ChezmoiStatus, ManagedFiles
from chezmoi_mousse.splash import FLOW_DIAGRAM


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
        "footer-background": BACKGROUND,
        "footer-description-background": BACKGROUND,
        "footer-item-background": BACKGROUND,
        "footer-key-background": BACKGROUND,
        "link-background": BACKGROUND,
        "scrollbar-corner-color": BACKGROUND,
    },
)


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loader": LoadingScreen,
    }

    BINDINGS = [
        ("s, S", "toggle_sidebar", "Toggle Sidebar"),
    ]
    # show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header()
        # yield SlideBar()
        with TabbedContent(
            "Diagram",
            "Doctor",
            "Dump-Config",
            "Chezmoi-Status",
            "Managed-Files",
            "Template-Data",
            "Cat-Config",
            "Git-Log",
            "Ignored",
            "Git-Status",
            "Unmanaged",
        ):
            # pylint: disable=no-member
            yield Static(FLOW_DIAGRAM, id="diagram")
            yield ChezmoiDoctor()
            yield Pretty(chezmoi.dump_config.dict_out)
            yield ChezmoiStatus()
            yield ManagedFiles()
            yield Pretty(chezmoi.data.dict_out)
            yield Pretty(chezmoi.cat_config.std_out)
            yield Pretty(chezmoi.git_log.list_out)
            yield Pretty(chezmoi.ignored.list_out)
            yield Pretty(chezmoi.status.list_out)
            yield Pretty(chezmoi.unmanaged.list_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "- o p e r a t e -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loader")
