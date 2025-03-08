from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Collapsible,
    Footer,
    Header,
    Label,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import FLOW, chezmoi, oled_dark_zen
from chezmoi_mousse.operator import ChezmoiDoctor
from chezmoi_mousse.splash import LoadingScreen


class SlideBar(Widget):

    # def __init__(self, highlight: bool = False):
    #     super().__init__()
    #     self.animate = True
    #     self.auto_scroll = True
    #     self.highlight = highlight
    #     self.id = "slidebar"
    #     self.markup = True
    #     self.max_lines = 160  # (80×3÷2)×((16−4)÷9)
    #     self.wrap = True

    def compose(self) -> ComposeResult:
        yield Label("Outputs from chezmoi commands:")
        with Collapsible(title="chezmoi dump-config"):
            yield VerticalScroll(Pretty(chezmoi.dump_config.py_out))
        with Collapsible(title="chezmoi data (template data)"):
            yield VerticalScroll(Pretty(chezmoi.template_data.py_out))
        with Collapsible(title="chezmoi ignored (git ignore in source-dir)"):
            yield VerticalScroll(Pretty(chezmoi.ignored.py_out))
        with Collapsible(title="chezmoi cat-config (contents of config-file)"):
            yield VerticalScroll(Pretty(chezmoi.cat_config.py_out))


class ChezmoiTUI(App):

    BINDINGS = {("i, I", "toggle_slidebar", "Inspect")}

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    show_sidebar = reactive(True)

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        yield SlideBar()
        with TabbedContent(
            # "Managed-Files",
            "Doctor",
            "Diagram",
            "Chezmoi-Status",
            "Unmanaged",
            "Git-Log",
            "Git-Status",
        ):
            # yield ManagedFiles(chezmoi.dest_dir)
            yield VerticalScroll(ChezmoiDoctor())
            yield Static(FLOW, id="diagram")
            yield Pretty(chezmoi.chezmoi_status.py_out)
            yield Pretty(chezmoi.unmanaged.py_out)
            yield Pretty(chezmoi.git_log.py_out)
            yield Pretty(chezmoi.git_status.py_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading", self.refresh_app)

    # Screen dismiss from the loading screen, returns something, so adding an
    # underscore to avoid exception saying refresh_app takes only one argument.
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")
