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
from chezmoi_mousse.button_groups import OperateBtnHorizontal
from chezmoi_mousse.chezmoi import Chezmoi
from chezmoi_mousse.constants import (
    Area,
    Chars,
    TabName,
    TcssStr,
    TreeName,
    ViewName,
)
from chezmoi_mousse.id_typing import (
    Id,
    OperateBtn,
    OperateHelp,
    SplashReturnData,
)
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    ConfigTab,
    DoctorTab,
    InitTab,
    LogsTab,
    ReAddTab,
)
from chezmoi_mousse.messages import OperateDataMsg
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


class ChezmoiGUI(App["ChezmoiGUI"]):
    def __init__(self):
        self.chezmoi = Chezmoi()
        self.destDir = self.chezmoi.destDir
        self.sourceDir = self.chezmoi.sourceDir
        super().__init__()

    CSS_PATH = "data/gui.tcss"

    BINDINGS = [
        Binding(key="M,m", action="maximize", description="maximize"),
        Binding(
            key="T,t",
            action="toggle_switch_slider",
            description="toggle-switches",
        ),
    ]

    def compose(self) -> ComposeResult:
        yield Header(icon=Chars.burger)
        with TabbedContent():
            with TabPane("Apply", id=Id.apply.tab_pane_id):
                yield ApplyTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.apply,
                    buttons=(
                        OperateBtn.apply_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane("Re-Add", id=Id.re_add.tab_pane_id):
                yield ReAddTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.re_add,
                    buttons=(
                        OperateBtn.re_add_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane("Add", id=Id.add.tab_pane_id):
                yield AddTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.add,
                    buttons=(OperateBtn.add_file, OperateBtn.add_dir),
                )
            with TabPane("Init", id=Id.init.tab_pane_id):
                yield InitTab()
            with TabPane("Logs", id=Id.logs.tab_pane_id):
                yield LogsTab()
            with TabPane("Config", id=Id.doctor.tab_pane_id):
                yield ConfigTab()
            with TabPane("Doctor", id=Id.config.tab_pane_id):
                yield DoctorTab()
        yield Footer()

    def on_mount(self) -> None:
        self.chezmoi.app_log.success("App initialized successfully")
        # TODO: inform user only file mode is supported if detected in the user config
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.custom_theme.chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse.custom_theme.chezmoi_mousse_dark)
        theme_name = "chezmoi-mousse-dark"
        self.theme = theme_name
        self.chezmoi.app_log.success(f"Theme set to {theme_name}")
        if self.chezmoi.init_cfg.chezmoi_found:
            self.chezmoi.app_log.success(
                f"chezmoi command found: {self.chezmoi.init_cfg.chezmoi_found}"
            )
        self.chezmoi.app_log.warning("Start loading screen")
        self.push_screen(LoadingScreen(), callback=self.handle_return_data)
        self.watch(self, "theme", self.on_theme_change, init=False)

        if self.chezmoi.init_cfg.changes_enabled:
            self.notify(
                OperateHelp.changes_mode_enabled.value, severity="warning"
            )

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.custom_theme.vars = (
            new_theme_object.to_color_system().generate()
        )
        self.chezmoi.app_log.success(f"Theme set to {new_theme}")

    def handle_return_data(self, return_data: SplashReturnData | None) -> None:
        if return_data is None:
            # Handle the case where no data was returned (though this shouldn't happen in your case)
            self.chezmoi.app_log.error("No data returned from splash screen")
            return
        if not self.chezmoi.init_cfg.chezmoi_found:
            self.push_screen(InstallHelp())
            return
        self.chezmoi.app_log.success("--- splash.py finished loading ---")
        # Populate Doctor DataTable
        doctor_tab = self.query_exactly_one(DoctorTab)
        doctor_tab.doctor_output = return_data.doctor
        doctor_tab.populate_doctor_data()
        # Cache outputs
        self.chezmoi.managed_dirs = return_data.managed_dirs
        self.chezmoi.managed_files = return_data.managed_files
        self.chezmoi.dir_status_lines = return_data.dir_status_lines
        self.chezmoi.file_status_lines = return_data.file_status_lines
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

    @on(OperateDataMsg)
    def handle_operate_result(self, message: OperateDataMsg) -> None:
        assert isinstance(message.dismiss_data.path, Path)
        managed_trees = self.query(ManagedTree)
        for tree in managed_trees:
            tree.remove_node_path(node_path=message.dismiss_data.path)
        flat_trees = self.query(FlatTree)
        for tree in flat_trees:
            tree.remove_node_path(node_path=message.dismiss_data.path)
        expanded_trees = self.query(ExpandedTree)
        for tree in expanded_trees:
            tree.remove_node_path(node_path=message.dismiss_data.path)
        self.query_one(FilteredDirTree).reload()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
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
        active_pane_id = self.query_one(TabbedContent).active
        tab_ids = Id.get_tab_ids_from_pane_id(pane_id=active_pane_id)

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
        else:
            self.notify("Cannot maximize this widget", severity="error")
            return

        self.push_screen(
            Maximized(
                tab_ids=tab_ids,
                id_to_maximize=id_to_maximize,
                path=current_path,
            )
        )

    @on(Button.Pressed, f".{TcssStr.operate_button}")
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
