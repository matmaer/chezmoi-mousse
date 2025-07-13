import os
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.scrollbar import ScrollBar
from textual.theme import Theme
from textual.widget import Widget
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
    ButtonEnum,
    CharsEnum,
    IdMixin,
    Location,
    PaneEnum,
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

    # reactive var to track the current tab and refresh bindings when changed
    active_pane = reactive("apply", bindings=True)

    def compose(self) -> ComposeResult:
        yield Header(icon=CharsEnum.burger.value)
        with TabbedContent():
            with TabPane("Apply", id=PaneEnum.apply.name):
                yield ApplyTab(tab_name=TabStr.apply_tab)
                yield ButtonsHorizontal(
                    TabStr.apply_tab,
                    buttons=(
                        ButtonEnum.apply_file_btn,
                        ButtonEnum.forget_file_btn,
                        ButtonEnum.destroy_file_btn,
                    ),
                    location=Location.bottom,
                )
            with TabPane("Re-Add", id=PaneEnum.re_add.name):
                yield ReAddTab(tab_name=TabStr.re_add_tab)
                yield ButtonsHorizontal(
                    TabStr.re_add_tab,
                    buttons=(
                        ButtonEnum.re_add_file_btn,
                        ButtonEnum.forget_file_btn,
                        ButtonEnum.destroy_file_btn,
                    ),
                    location=Location.bottom,
                )
            with TabPane("Add", id=PaneEnum.add.name):
                yield AddTab(tab_name=TabStr.add_tab)
                yield ButtonsHorizontal(
                    TabStr.add_tab,
                    buttons=(ButtonEnum.add_file_btn, ButtonEnum.add_dir_btn),
                    location=Location.bottom,
                )
            with TabPane("Init", id=PaneEnum.init.name):
                yield InitTab(tab_name=TabStr.init_tab)
            with TabPane("Doctor", id=PaneEnum.doctor.name):
                yield DoctorTab(tab_name=TabStr.doctor_tab)
            with TabPane("Log", id=PaneEnum.log.name):
                yield cmd_log

        yield Footer()

    def on_mount(self) -> None:
        if os.environ.get("MOUSSE_DEV") == "1":
            self.notify("Running in development mode", severity="information")
        if os.environ.get("MOUSSE_ENABLE_CHANGES") == "1":
            self.notify(
                "Changes mode enabled, operations will be executed",
                severity="warning",
            )
        add_dir_btn = self.query_one(
            IdMixin(TabStr.add_tab).button_qid(ButtonEnum.add_dir_btn), Button
        )
        add_dir_btn.disabled = True

        cmd_log.log_success("App initialized successfully")
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.theme.chezmoi_mousse_dark)
        theme_name = "chezmoi-mousse-dark"
        self.theme = theme_name
        cmd_log.log_success(f"Theme set to {theme_name}")
        cmd_log.log_warning("starting loading screen")
        self.push_screen(LoadingScreen(), callback=self.first_mount_refresh)
        self.watch(self, "theme", self.on_theme_change, init=False)

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.app.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.theme.vars = (
            new_theme_object.to_color_system().generate()
        )
        cmd_log.log_success(f"Theme set to {new_theme}")

    def first_mount_refresh(self, _: object) -> None:
        # Refresh Tree widgets
        tab_tree_cls_list: list[
            tuple[TabStr, TreeStr, type[ManagedTree | FlatTree | ExpandedTree]]
        ] = [
            (TabStr.apply_tab, TreeStr.managed_tree, ManagedTree),
            (TabStr.apply_tab, TreeStr.flat_tree, FlatTree),
            (TabStr.apply_tab, TreeStr.expanded_tree, ExpandedTree),
            (TabStr.re_add_tab, TreeStr.managed_tree, ManagedTree),
            (TabStr.re_add_tab, TreeStr.flat_tree, FlatTree),
            (TabStr.re_add_tab, TreeStr.expanded_tree, ExpandedTree),
        ]
        for tab, tree, tree_cls in tab_tree_cls_list:
            self.query_one(
                IdMixin(tab).tree_qid(tree), tree_cls
            ).refresh_tree_data()
        # Refresh DirectoryTree
        self.query_one(FilteredDirTree).reload()
        # Refresh DoctorTab
        self.query_one(DoctorTab).populate_doctor_data()

    @on(OperateMessage)
    def handle_operate_result(self, message: OperateMessage) -> None:

        for tree_cls in (ManagedTree, FlatTree, ExpandedTree):
            for tree in self.query(tree_cls):
                tree.remove_node_path(path=message.dismiss_data.path)

        self.query_one(FilteredDirTree).reload()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self.active_pane = event.tab.id

        # Refresh bindings on the newly activated tab to ensure they reflect current state
        if event.tab.id in ("apply", "re_add"):
            # Get the tab widget and refresh its bindings
            tab_pane = self.query_one(f"#{event.tab.id}", TabPane)
            if tab_pane.children:
                tab_widget = tab_pane.children[0]
                # Focus the tab widget and use call_after_refresh to ensure mounting is complete
                tab_widget.focus()
                if hasattr(tab_widget, "refresh_bindings"):
                    self.call_after_refresh(tab_widget.refresh_bindings)

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:

        active_pane = self.query_one(TabbedContent).active

        if action == "maximize":
            # If no tab is active, return True because ApplyTab will be shown
            if not active_pane:
                return True
            # Once the app is running - guard against empty active_pane
            try:
                id_mixin = IdMixin(PaneEnum[active_pane].value)
            except (KeyError, AttributeError):
                return True
            if (
                id_mixin.tab_name == TabStr.doctor_tab
                or id_mixin.tab_name == TabStr.log_tab
            ):
                return None  # show disabled binding
            return True

        elif action == "toggle_filter_slider":

            if not active_pane:
                return True  # Show at startup (apply tab will be active)
            if active_pane in ("apply", "re_add", "add"):
                return True
            else:
                return None  # show disabled binding

        return True  # show disabled binding

    def action_toggle_filter_slider(self) -> None:
        # merely find the corresponding method in the active tab ant call it
        active_pane = self.query_one(TabbedContent).active
        if active_pane in ("apply", "re_add", "add"):
            tab_pane = self.query_one(f"#{active_pane}", TabPane)
            tab_widget = tab_pane.children[0]
            if hasattr(tab_widget, "action_toggle_filter_slider"):
                getattr(tab_widget, "action_toggle_filter_slider")()

    def action_maximize(self) -> None:
        active_pane = self.query_one(TabbedContent).active
        # tab id not known upon MainScreen init, so we init it here.
        id_mixin = IdMixin(PaneEnum[active_pane].value)

        # Initialize modal parameters
        tab_name = PaneEnum[active_pane].value
        id_to_maximize: str | None = None
        path_for_maximize: Path | None = None

        if id_mixin.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            # Determine what view to show in the modal
            content_switcher_right = self.query_one(
                id_mixin.content_switcher_qid(Location.right), ContentSwitcher
            )
            current_view_id: str | None = content_switcher_right.current

            if current_view_id:
                right_switcher_widget: Widget | None = (
                    content_switcher_right.get_child_by_id(current_view_id)
                )
                id_to_maximize = current_view_id
                path_for_maximize = getattr(right_switcher_widget, "path")

        elif id_mixin.tab_name == TabStr.add_tab:
            add_tab_contents_view = self.query_one(
                id_mixin.view_qid(ViewStr.contents_view), ContentsView
            )

            id_to_maximize = add_tab_contents_view.id
            path_for_maximize = getattr(add_tab_contents_view, "path")

        self.app.push_screen(
            Maximized(
                tab_name=tab_name,
                id_to_maximize=id_to_maximize,
                path=path_for_maximize,
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        active_pane = self.query_one(TabbedContent).active
        id_mixin = IdMixin(PaneEnum[active_pane].value)
        contents_view = self.query_one(
            id_mixin.view_qid(ViewStr.contents_view), ContentsView
        )
        current_path = getattr(contents_view, "path")

        if current_path == CM_CFG.destDir:
            self.notify(
                "Operation not possible for destDir.", severity="error"
            )
            return

        if event.button.id == id_mixin.button_id(ButtonEnum.apply_file_btn):
            self.push_screen(
                Operate(
                    id_mixin.tab_name,
                    path=current_path,
                    buttons=(
                        ButtonEnum.apply_file_btn,
                        ButtonEnum.operate_dismiss_btn,
                    ),
                )
            )
        elif event.button.id == id_mixin.button_id(ButtonEnum.re_add_file_btn):
            self.push_screen(
                Operate(
                    id_mixin.tab_name,
                    buttons=(
                        ButtonEnum.re_add_file_btn,
                        ButtonEnum.operate_dismiss_btn,
                    ),
                    path=current_path,
                )
            )
        elif event.button.id == id_mixin.button_id(ButtonEnum.add_file_btn):
            self.push_screen(
                Operate(
                    id_mixin.tab_name,
                    buttons=(
                        ButtonEnum.add_file_btn,
                        ButtonEnum.operate_dismiss_btn,
                    ),
                    path=current_path,
                )
            )
        elif event.button.id == id_mixin.button_id(ButtonEnum.forget_file_btn):
            self.push_screen(
                Operate(
                    id_mixin.tab_name,
                    buttons=(
                        ButtonEnum.forget_file_btn,
                        ButtonEnum.operate_dismiss_btn,
                    ),
                    path=current_path,
                )
            )
        elif event.button.id == id_mixin.button_id(
            ButtonEnum.destroy_file_btn
        ):
            self.push_screen(
                Operate(
                    id_mixin.tab_name,
                    buttons=(
                        ButtonEnum.destroy_file_btn,
                        ButtonEnum.operate_dismiss_btn,
                    ),
                    path=current_path,
                )
            )
