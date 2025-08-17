from pathlib import Path
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.scrollbar import ScrollBar
from textual.theme import Theme
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
    TabbedContent,
    TabPane,
)

import chezmoi_mousse.theme
from chezmoi_mousse.chezmoi import CM_CFG, cmd_log
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import (
    Buttons,
    Chars,
    Id,
    IdMixin,
    Location,
    TabStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    DoctorTab,
    InitTab,
    ReAddTab,
)
from chezmoi_mousse.messages import OperateMessage
from chezmoi_mousse.overrides import CustomScrollBarRender
from chezmoi_mousse.screens import Maximized, Operate
from chezmoi_mousse.splash import LoadingScreen
from chezmoi_mousse.widgets import (
    ContentsView,
    ExpandedTree,
    FilteredDirTree,
    FlatTree,
    ManagedTree,
)


class ChezmoiGUI(App[None]):

    CSS_PATH = "gui.tcss"

    BINDINGS = [
        Binding(key="M,m", action="maximize", description="maximize"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.pane_id_map: dict[str, IdMixin] = {
            Id.apply.tab_pane_id: Id.apply,
            Id.re_add.tab_pane_id: Id.re_add,
            Id.add.tab_pane_id: Id.add,
            Id.doctor.tab_pane_id: Id.doctor,
            Id.init.tab_pane_id: Id.init,
        }

    def compose(self) -> ComposeResult:
        yield Header(icon=Chars.burger.value)
        with TabbedContent():
            with TabPane("Apply", id=Id.apply.tab_pane_id):
                yield ApplyTab()
                yield ButtonsHorizontal(
                    TabStr.apply_tab,
                    buttons=(
                        Buttons.apply_file_btn,
                        Buttons.forget_file_btn,
                        Buttons.destroy_file_btn,
                    ),
                    location=Location.bottom,
                )
            with TabPane("Re-Add", id=Id.re_add.tab_pane_id):
                yield ReAddTab()
                yield ButtonsHorizontal(
                    TabStr.re_add_tab,
                    buttons=(
                        Buttons.re_add_file_btn,
                        Buttons.forget_file_btn,
                        Buttons.destroy_file_btn,
                    ),
                    location=Location.bottom,
                )
            with TabPane("Add", id=Id.add.tab_pane_id):
                yield AddTab()
                yield ButtonsHorizontal(
                    TabStr.add_tab,
                    buttons=(Buttons.add_file_btn, Buttons.add_dir_btn),
                    location=Location.bottom,
                )
            with TabPane("Init", id=Id.init.tab_pane_id):
                yield InitTab()
            with TabPane("Doctor", id=Id.doctor.tab_pane_id):
                yield DoctorTab()
            with TabPane("Log", id=Id.log.tab_pane_id):
                yield cmd_log

        yield Footer()

    def on_mount(self) -> None:
        cmd_log.log_success("App initialized successfully")
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.theme.chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse.theme.chezmoi_mousse_dark)
        theme_name = "chezmoi-mousse-dark"
        self.theme = theme_name
        cmd_log.log_success(f"Theme set to {theme_name}")
        cmd_log.log_warning("Start loading screen")
        self.push_screen(LoadingScreen(), callback=self.first_mount_refresh)
        self.watch(self, "theme", self.on_theme_change, init=False)

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.theme.vars = (
            new_theme_object.to_color_system().generate()
        )
        cmd_log.log_success(f"Theme set to {new_theme}")

    def first_mount_refresh(self, _: object) -> None:
        add_dir_btn = self.query_one(
            Id.add.button_qid(Buttons.add_dir_btn), Button
        )
        add_dir_btn.disabled = True
        # Trees to refresh for each tab
        tree_types: list[
            tuple[TreeStr, type[ManagedTree | FlatTree | ExpandedTree]]
        ] = [
            (TreeStr.managed_tree, ManagedTree),
            (TreeStr.flat_tree, FlatTree),
            (TreeStr.expanded_tree, ExpandedTree),
        ]
        # Refresh apply and re_add trees
        for tab_ids in (Id.apply, Id.re_add):
            # id_mixin = self.pane_id_map[tab_name]
            for tree_str, tree_cls in tree_types:
                self.query_one(
                    tab_ids.tree_qid(tree_str), tree_cls
                ).refresh_tree_data()
        # Refresh DirectoryTree
        self.query_one(FilteredDirTree).reload()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self.refresh_bindings()

    @on(OperateMessage)
    def handle_operate_result(self, message: OperateMessage) -> None:

        for tree_cls in (ManagedTree, FlatTree, ExpandedTree):
            for tree in self.query(tree_cls):
                tree.remove_node_path(node_path=message.dismiss_data.path)

        self.query_one(FilteredDirTree).reload()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:

        if action == "maximize":
            if self.query_one(TabbedContent).active in (
                Id.doctor.tab_pane_id,
                Id.log.tab_pane_id,
                Id.init.tab_pane_id,
            ):
                return None
            return True

        elif action == "toggle_filter_slider":
            if self.query_one(TabbedContent).active in (
                Id.apply.tab_pane_id,
                Id.re_add.tab_pane_id,
                Id.add.tab_pane_id,
            ):
                return True
            return None

        return True

    def action_toggle_filter_slider(self) -> None:
        # merely find the corresponding method in the active tab ant call it
        tab_pane = self.query_one(
            f"#{self.query_one(TabbedContent).active}", TabPane
        )
        tab_widget = tab_pane.children[0]
        if hasattr(tab_widget, "action_toggle_filter_slider"):
            getattr(tab_widget, "action_toggle_filter_slider")()  # call it

    def action_maximize(self) -> None:
        id_mixin = self.pane_id_map[self.query_one(TabbedContent).active]

        # Initialize modal parameters
        id_to_maximize: str | None = None
        current_path: Path = CM_CFG.destDir

        if id_mixin.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            # Determine what view to show in the modal
            id_to_maximize = self.query_one(
                id_mixin.content_switcher_qid(Location.right), ContentSwitcher
            ).current
            active_widget = self.query_one(f"#{id_to_maximize}")
            current_path = getattr(active_widget, "path")

        elif id_mixin.tab_name == TabStr.add_tab:
            add_tab_contents_view = self.query_one(
                id_mixin.view_qid(ViewStr.contents_view), ContentsView
            )

            id_to_maximize = add_tab_contents_view.id
            current_path = getattr(add_tab_contents_view, "path")

        self.push_screen(
            Maximized(
                tab_name=id_mixin.tab_name,
                id_to_maximize=id_to_maximize,
                path=current_path,
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        id_mixin = self.pane_id_map[self.query_one(TabbedContent).active]
        contents_view = self.query_one(
            id_mixin.view_qid(ViewStr.contents_view), ContentsView
        )
        current_path = getattr(contents_view, "path")

        if event.button.label in (
            Buttons.apply_file_btn.value,
            Buttons.re_add_file_btn.value,
            Buttons.add_file_btn.value,
            Buttons.forget_file_btn.value,
            Buttons.destroy_file_btn.value,
        ):
            btn_enum = Buttons(event.button.label)
            self.push_screen(
                Operate(
                    id_mixin.tab_name,
                    path=current_path,
                    buttons=(btn_enum, Buttons.operate_dismiss_btn),
                )
            )
