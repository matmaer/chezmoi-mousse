import os
from pathlib import Path

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
    Chars,
    Id,
    Location,
    OperateBtn,
    OperateHelp,
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
from chezmoi_mousse.messages import InvalidInputMessage, OperateMessage
from chezmoi_mousse.overrides import CustomScrollBarRender
from chezmoi_mousse.screens import InvalidInputModal, Maximized, Operate
from chezmoi_mousse.splash import LoadingScreen
from chezmoi_mousse.widgets import (
    ContentsView,
    ExpandedTree,
    FilteredDirTree,
    FlatTree,
    ManagedTree,
)


class ChezmoiGUI(App[None]):
    def __init__(self):
        super().__init__()
        self.loading_screen_dismissed = False

    CSS_PATH = "gui.tcss"

    BINDINGS = [
        Binding(key="M,m", action="maximize", description="maximize"),
        Binding(
            key="T,t",
            action="toggle_switch_slider",
            description="toggle-switches",
        ),
    ]

    def compose(self) -> ComposeResult:
        yield Header(icon=Chars.burger.value)
        with TabbedContent():
            with TabPane("Apply", id=Id.apply.tab_pane_id):
                yield ApplyTab()
                yield ButtonsHorizontal(
                    tab_ids=Id.apply,
                    buttons=(
                        OperateBtn.apply_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                    location=Location.bottom,
                )
            with TabPane("Re-Add", id=Id.re_add.tab_pane_id):
                yield ReAddTab()
                yield ButtonsHorizontal(
                    tab_ids=Id.re_add,
                    buttons=(
                        OperateBtn.re_add_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                    location=Location.bottom,
                )
            with TabPane("Add", id=Id.add.tab_pane_id):
                yield AddTab()
                yield ButtonsHorizontal(
                    tab_ids=Id.add,
                    buttons=(OperateBtn.add_file, OperateBtn.add_dir),
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

        if os.environ.get("MOUSSE_ENABLE_CHANGES") == "1":
            self.notify(
                OperateHelp.changes_mode_enabled.value, severity="warning"
            )

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.theme.vars = (
            new_theme_object.to_color_system().generate()
        )
        cmd_log.log_success(f"Theme set to {new_theme}")

    def first_mount_refresh(self, _: object) -> None:
        add_dir = self.query_one(Id.add.button_qid(OperateBtn.add_dir), Button)
        add_dir.disabled = True
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
            for tree_str, tree_cls in tree_types:
                self.query_one(
                    tab_ids.tree_qid(tree_str), tree_cls
                ).refresh_tree_data()
        # Refresh DirectoryTree
        self.query_one(FilteredDirTree).reload()
        self.loading_screen_dismissed = True

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

    @on(InvalidInputMessage)
    def handle_invalid_input(self, message: InvalidInputMessage) -> None:
        self.push_screen(InvalidInputModal(descriptions=message.reasons))

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        # Prevent actions before loading screen is dismissed
        if not self.loading_screen_dismissed:
            return None
        if action == "maximize":
            if self.query_one(TabbedContent).active in (
                Id.doctor.tab_pane_id,
                Id.log.tab_pane_id,
                Id.init.tab_pane_id,
            ):
                return None
            return True
        elif action == "toggle_switch_slider":
            if self.query_one(TabbedContent).active in (
                Id.apply.tab_pane_id,
                Id.re_add.tab_pane_id,
                Id.add.tab_pane_id,
                Id.init.tab_pane_id,
            ):
                return True
            return None

        return True

    def action_toggle_switch_slider(self) -> None:
        # merely find the corresponding method in the active tab ant call it
        tab_pane = self.query_one(
            f"#{self.query_one(TabbedContent).active}", TabPane
        )
        tab_widget = tab_pane.children[0]
        if hasattr(tab_widget, "action_toggle_switch_slider"):
            getattr(tab_widget, "action_toggle_switch_slider")()  # call it

    def action_maximize(self) -> None:
        active_pane_id = self.query_one(TabbedContent).active
        tab_ids = Id.get_tab_ids_from_pane_id(pane_id=active_pane_id)

        # Initialize modal parameters
        id_to_maximize: str | None = None
        current_path: Path = CM_CFG.destDir

        if tab_ids.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            # Determine what view to show in the modal
            id_to_maximize = self.query_one(
                tab_ids.content_switcher_qid(Location.right), ContentSwitcher
            ).current
            active_widget = self.query_one(f"#{id_to_maximize}")
            current_path = getattr(active_widget, "path")

        elif tab_ids.tab_name == TabStr.add_tab:
            add_tab_contents_view = self.query_one(
                tab_ids.view_qid(ViewStr.contents_view), ContentsView
            )

            id_to_maximize = add_tab_contents_view.id
            current_path = getattr(add_tab_contents_view, "path")

        self.push_screen(
            Maximized(
                tab_ids=tab_ids,
                id_to_maximize=id_to_maximize,
                path=current_path,
            )
        )

    @on(Button.Pressed, ".operate_button")
    def handle_push_operate_modal(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label not in (
            OperateBtn.apply_file.value,
            OperateBtn.re_add_file.value,
            OperateBtn.add_file.value,
            OperateBtn.forget_file.value,
            OperateBtn.destroy_file.value,
        ):
            return
        active_pane_id = self.query_one(TabbedContent).active
        tab_ids = Id.get_tab_ids_from_pane_id(pane_id=active_pane_id)
        # handle Add tab operation button
        if tab_ids.tab_name == TabStr.add_tab:
            add_tab_contents_view = self.query_one(
                tab_ids.view_qid(ViewStr.contents_view), ContentsView
            )
            current_path = getattr(add_tab_contents_view, "path")
        # handle Apply and Re-Add tab operation button
        else:
            current_view_id = self.query_one(
                tab_ids.content_switcher_qid(Location.right), ContentSwitcher
            ).current
            current_view = self.query_one(f"#{current_view_id}")
            current_path = getattr(current_view, "path")

        btn_enum = OperateBtn(event.button.label)
        self.push_screen(
            Operate(
                tab_ids=tab_ids,
                path=current_path,
                buttons=(btn_enum, OperateBtn.operate_dismiss),
            )
        )
