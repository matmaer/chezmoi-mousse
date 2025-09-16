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

import chezmoi_mousse.custom_theme
from chezmoi_mousse.chezmoi import (
    CHEZMOI_COMMAND_FOUND,
    app_log,
    chezmoi,
    init_log,
)
from chezmoi_mousse.constants import (
    Area,
    BorderTitle,
    Chars,
    TabBtn,
    TabName,
    TreeName,
    ViewName,
)
from chezmoi_mousse.containers import ButtonsHorizontal
from chezmoi_mousse.id_typing import Id, OperateBtn, OperateHelp
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    DoctorTab,
    InitTab,
    LogTab,
    ReAddTab,
)
from chezmoi_mousse.messages import InvalidInputMessage, OperateMessage
from chezmoi_mousse.overrides import CustomScrollBarRender
from chezmoi_mousse.screens import InstallHelp, Maximized, Operate
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
        self.loading_screen_dismissed = False
        super().__init__()

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
                    area=Area.bottom,
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
                    area=Area.bottom,
                )
            with TabPane("Add", id=Id.add.tab_pane_id):
                yield AddTab()
                yield ButtonsHorizontal(
                    tab_ids=Id.add,
                    buttons=(OperateBtn.add_file, OperateBtn.add_dir),
                    area=Area.bottom,
                )
            with TabPane("Init", id=Id.init.tab_pane_id):
                yield InitTab()
            with TabPane("Doctor", id=Id.doctor.tab_pane_id):
                yield DoctorTab()
            with TabPane("Logs", id=Id.logs.tab_pane_id):
                yield LogTab()
        yield Header(icon=Chars.burger)
        yield Footer()

    def on_mount(self) -> None:
        app_log.log_success("App initialized successfully")
        if not CHEZMOI_COMMAND_FOUND:
            app_log.log_error("chezmoi command not found")
            self.push_screen(InstallHelp())
            return
        else:
            app_log.log_success(
                f"chezmoi command found: {CHEZMOI_COMMAND_FOUND}"
            )
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.custom_theme.chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse.custom_theme.chezmoi_mousse_dark)
        theme_name = "chezmoi-mousse-dark"
        self.theme = theme_name
        app_log.log_success(f"Theme set to {theme_name}")
        app_log.log_warning("Start loading screen")
        self.push_screen(LoadingScreen(), callback=self.first_mount_refresh)
        self.watch(self, "theme", self.on_theme_change, init=False)

        if os.environ.get("MOUSSE_ENABLE_CHANGES") == "1":
            self.notify(
                OperateHelp.changes_mode_enabled.value, severity="warning"
            )

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.custom_theme.vars = (
            new_theme_object.to_color_system().generate()
        )
        app_log.log_success(f"Theme set to {new_theme}")

    def first_mount_refresh(self, _: object) -> None:
        self.loading_screen_dismissed = True
        app_log.log_success("--- splash.py finished loading ---")
        # Trees to refresh for each tab
        tree_types: list[
            tuple[TreeName, type[ManagedTree | FlatTree | ExpandedTree]]
        ] = [
            (TreeName.managed_tree, ManagedTree),
            (TreeName.flat_tree, FlatTree),
            (TreeName.expanded_tree, ExpandedTree),
        ]
        # Refresh apply and re_add trees
        for tab_ids in (Id.apply, Id.re_add):
            for tree_name, tree_cls in tree_types:
                self.query_one(
                    tab_ids.tree_id("#", tree=tree_name), tree_cls
                ).refresh_tree_data()
        # Refresh DirectoryTree
        self.query_one(FilteredDirTree).reload()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self.refresh_bindings()

    @on(OperateMessage)
    def handle_operate_result(self, message: OperateMessage) -> None:
        assert isinstance(message.dismiss_data.path, Path)
        for tree_cls in (ManagedTree, FlatTree, ExpandedTree):
            for tree in self.query(tree_cls):
                tree.remove_node_path(node_path=message.dismiss_data.path)

        self.query_one(FilteredDirTree).reload()

    @on(InvalidInputMessage)
    def handle_invalid_input(self, message: InvalidInputMessage) -> None:
        text_lines = "\n".join(message.reasons)
        init_log.log_warning(f"Invalid input detected: {text_lines}")

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        # Prevent actions before loading screen is dismissed
        if not self.loading_screen_dismissed:
            return None
        if action == "maximize":
            if self.query_one(TabbedContent).active in (
                Id.doctor.tab_pane_id,
                Id.logs.tab_pane_id,
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
        tab_widget = self.query_one(
            f"#{self.query_one(TabbedContent).active}", TabPane
        ).children[0]
        if hasattr(tab_widget, "action_toggle_switch_slider"):
            getattr(tab_widget, "action_toggle_switch_slider")()  # call it

    def action_maximize(self) -> None:
        if not self.loading_screen_dismissed:
            return
        active_pane_id = self.query_one(TabbedContent).active
        tab_ids = Id.get_tab_ids_from_pane_id(pane_id=active_pane_id)

        # Initialize screen parameters
        id_to_maximize: str | None = None
        current_path: Path | None = chezmoi.destDir

        if tab_ids.tab_name in (TabName.apply_tab, TabName.re_add_tab):
            # Determine what view to show in the screen
            id_to_maximize = self.query_one(
                tab_ids.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            active_widget = self.query_one(f"#{id_to_maximize}")
            current_path = getattr(active_widget, "path")

        elif tab_ids.tab_name == TabName.add_tab:
            add_tab_contents_view = self.query_one(
                tab_ids.view_id("#", view=ViewName.contents_view), ContentsView
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
    def handle_push_operate_screen(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label not in (
            OperateBtn.apply_file,
            OperateBtn.re_add_file,
            OperateBtn.add_file,
            OperateBtn.forget_file,
            OperateBtn.destroy_file,
        ):
            return
        active_pane_id = self.query_one(TabbedContent).active
        tab_ids = Id.get_tab_ids_from_pane_id(pane_id=active_pane_id)
        # handle Add tab operation button
        if tab_ids.tab_name == TabName.add_tab:
            add_tab_contents_view = self.query_one(
                tab_ids.view_id("#", view=ViewName.contents_view), ContentsView
            )
            current_path = getattr(add_tab_contents_view, "path")
        # handle Apply and Re-Add tab operation button
        else:
            current_view_id = self.query_one(
                tab_ids.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            current_view = self.query_one(f"#{current_view_id}")
            current_path = getattr(current_view, "path")

        self.push_screen(
            Operate(
                tab_ids=tab_ids,
                path=current_path,
                buttons=(
                    OperateBtn(event.button.label),
                    OperateBtn.operate_dismiss,
                ),
            )
        )

    @on(Button.Pressed, ".tab_button")
    def handle_logs_tab_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label not in (TabBtn.app_log, TabBtn.output_log):
            return
        active_pane_id = self.query_one(TabbedContent).active
        tab_ids = Id.get_tab_ids_from_pane_id(pane_id=active_pane_id)
        # AppLog/OutputLog Content Switcher
        if event.button.id == tab_ids.button_id(btn=TabBtn.app_log):
            content_switcher = self.query_one(
                tab_ids.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            )
            content_switcher.current = tab_ids.view_id(
                view=ViewName.app_log_view
            )
            content_switcher.border_title = BorderTitle.app_log
        elif event.button.id == tab_ids.button_id(btn=TabBtn.output_log):
            content_switcher = self.query_one(
                tab_ids.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            )
            content_switcher.current = tab_ids.view_id(
                view=ViewName.output_log_view
            )
            content_switcher.border_title = BorderTitle.output_log
