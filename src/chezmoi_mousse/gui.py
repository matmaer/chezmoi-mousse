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
from chezmoi_mousse.directory_tree import FilteredDirTree
from chezmoi_mousse.id_typing import Id, SplashReturnData, TabIds
from chezmoi_mousse.id_typing.enums import (
    Area,
    Chars,
    LogName,
    OperateBtn,
    OperateHelp,
    TabName,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    ConfigTab,
    HelpTab,
    InitTab,
    LogsTab,
    ReAddTab,
)
from chezmoi_mousse.messages import OperateDismissMsg
from chezmoi_mousse.overrides import CustomScrollBarRender
from chezmoi_mousse.rich_logs import AppLog, ContentsView, DebugLog, OutputLog
from chezmoi_mousse.screens import InstallHelp, Maximized, Operate
from chezmoi_mousse.splash import LoadingScreen
from chezmoi_mousse.widgets import (
    DoctorListView,
    DoctorTable,
    ExpandedTree,
    FlatTree,
    ManagedTree,
)


class ChezmoiGUI(App[None]):
    def __init__(
        self,
        changes_enabled: bool,
        chezmoi_found: bool,
        dev_mode: bool,
        provisional_dest_dir: Path,
        provisional_source_dir: Path,
    ):
        self.changes_enabled = changes_enabled
        self.chezmoi_found = chezmoi_found
        self.destDir: Path = provisional_dest_dir
        self.dev_mode = dev_mode
        self.sourceDir: Path = provisional_source_dir

        self.app_log: AppLog | None = None
        self.output_log: OutputLog | None = None
        self.debug_log: DebugLog | None = None

        self.git_autoadd: bool = False
        self.git_autocommit: bool = False
        self.git_autopush: bool = False

        self.chezmoi = Chezmoi(changes_enabled=self.changes_enabled)

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
            with TabPane(TabName.apply_tab.value, id=TabName.apply_tab.name):
                yield ApplyTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.apply,
                    buttons=(
                        OperateBtn.apply_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(TabName.re_add_tab.value, id=TabName.re_add_tab.name):
                yield ReAddTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.re_add,
                    buttons=(
                        OperateBtn.re_add_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(TabName.add_tab.value, id=TabName.add_tab.name):
                yield AddTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.add,
                    buttons=(OperateBtn.add_file, OperateBtn.add_dir),
                )
            with TabPane(TabName.init_tab.value, id=TabName.init_tab.name):
                yield InitTab()
            with TabPane(TabName.logs_tab.value, id=TabName.logs_tab.name):
                yield LogsTab()
            with TabPane(TabName.config_tab.value, id=TabName.config_tab.name):
                yield ConfigTab()
            with TabPane(TabName.help_tab.value, id=TabName.help_tab.name):
                yield HelpTab()
        yield Footer()

    def on_mount(self) -> None:
        if self.app_log:
            self.app_log.success("App initialized successfully")
        # TODO: inform user only file mode is supported if detected in the user config
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse.custom_theme.chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse.custom_theme.chezmoi_mousse_dark)
        theme_name = "chezmoi-mousse-dark"
        self.theme = theme_name
        if self.app_log:
            self.app_log.success(f"Theme set to {theme_name}")
        if self.chezmoi_found and self.app_log:
            self.app_log.success(
                f"chezmoi command found: {self.chezmoi_found}"
            )
        if self.app_log:
            self.app_log.ready_to_run("--- Start loading screen ---")
        self.push_screen(
            LoadingScreen(), callback=self.run_post_splash_actions
        )
        self.watch(self, "theme", self.on_theme_change, init=False)

    def on_theme_change(self, _: str, new_theme: str) -> None:
        new_theme_object: Theme | None = self.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        chezmoi_mousse.custom_theme.vars = (
            new_theme_object.to_color_system().generate()
        )
        if self.app_log is not None:
            self.app_log.success(f"Theme set to {new_theme}")

    def run_post_splash_actions(
        self, return_data: SplashReturnData | None
    ) -> None:
        if return_data is None:
            if self.app_log is not None:
                self.app_log.error("No data returned from splash screen")
            return

        if not self.chezmoi_found:
            self.push_screen(InstallHelp())
            return
        if self.app_log is not None:
            self.app_log.ready_to_run("--- Loading screen completed ---")
        # Populate Doctor DataTable
        pw_mgr_cmds: list[str] = self.query_one(
            Id.config.datatable_qid, DoctorTable
        ).populate_doctor_data(return_data.doctor.splitlines())
        self.query_one(
            Id.config.listview_qid, DoctorListView
        ).populate_listview(pw_mgr_cmds)
        # refresh chezmoi managed and status data
        self.chezmoi.refresh_managed(return_data)
        # Trees to refresh for each tab
        trees: list[
            tuple[TreeName, type[ManagedTree | FlatTree | ExpandedTree]]
        ] = [
            (TreeName.managed_tree, ManagedTree),
            (TreeName.flat_tree, FlatTree),
            (TreeName.expanded_tree, ExpandedTree),
        ]
        # Refresh apply and re_add trees
        for tab_ids in (Id.apply, Id.re_add):
            for tree_name, tree_cls in trees:
                self.query_one(
                    tab_ids.tree_id("#", tree=tree_name), tree_cls
                ).refresh_tree_data()
        # Refresh DirectoryTree
        self.query_one(FilteredDirTree).reload()
        # make the app_log appear first time the main Logs tab is opened
        content_switcher = self.query_one(
            Id.logs.content_switcher_id("#", area=Area.top), ContentSwitcher
        )
        content_switcher.current = LogName.app_log.name
        if self.dev_mode:
            self.notify('Running in "dev mode"', severity="information")
        self.notify_changes_enabled()

    def notify_changes_enabled(self):
        # Notify app startup mode
        if self.changes_enabled:
            self.notify(
                OperateHelp.changes_mode_enabled.value, severity="warning"
            )
        else:
            self.notify(
                OperateHelp.changes_mode_disabled.value, severity="information"
            )

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self.refresh_bindings()

    @on(OperateDismissMsg)
    def handle_operate_result(self, message: OperateDismissMsg) -> None:
        assert isinstance(message.path, Path)
        managed_trees = self.query(ManagedTree)
        for tree in managed_trees:
            tree.remove_node_path(node_path=message.path)
        flat_trees = self.query(FlatTree)
        for tree in flat_trees:
            tree.remove_node_path(node_path=message.path)
        expanded_trees = self.query(ExpandedTree)
        for tree in expanded_trees:
            tree.remove_node_path(node_path=message.path)
        self.query_one(FilteredDirTree).reload()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == "maximize":
            if self.query_one(TabbedContent).active in (
                Id.config.tab_name,
                Id.logs.tab_name,
                Id.init.tab_name,
            ):
                return None
            return True
        if action == "toggle_switch_slider":
            if self.query_one(TabbedContent).active in (
                Id.apply.tab_name,
                Id.re_add.tab_name,
                Id.add.tab_name,
                Id.init.tab_name,
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
        current_path = self.destDir
        active_tab_id = self.query_one(TabbedContent).active
        id_to_maximize: str | None = None
        tab_ids: TabIds | None = None

        if active_tab_id == TabName.apply_tab.name:
            active_widget_id = self.query_one(
                Id.apply.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            active_widget = self.query_one(f"#{active_widget_id}")
            current_path = getattr(active_widget, "path")
            id_to_maximize = active_widget.id
            tab_ids = getattr(Id, "apply")

        elif active_tab_id == TabName.re_add_tab.name:
            # Determine what view to show in the screen
            active_widget_id = self.query_one(
                Id.re_add.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            active_widget = self.query_one(f"#{active_widget_id}")
            current_path = getattr(active_widget, "path")
            id_to_maximize = active_widget.id
            tab_ids = getattr(Id, "re_add")

        elif active_tab_id == TabName.add_tab.name:
            contents_view = self.query_one(
                Id.add.view_id("#", view=ViewName.contents_view), ContentsView
            )
            current_path = getattr(contents_view, "path")
            id_to_maximize = contents_view.id
            tab_ids = getattr(Id, "add")

        if tab_ids is None:
            self.notify("Cannot maximize this widget", severity="error")
            return
        self.push_screen(
            Maximized(
                tab_ids=tab_ids,
                id_to_maximize=id_to_maximize,
                path=current_path,
            )
        )

    @on(Button.Pressed, Tcss.operate_button.value)
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
        tab_ids: TabIds | None = None
        active_tab_id = self.query_one(TabbedContent).active
        # handle Add tab operation button
        if active_tab_id == TabName.add_tab.name:
            add_tab_contents_view = self.query_one(
                Id.add.view_id("#", view=ViewName.contents_view), ContentsView
            )
            current_path = getattr(add_tab_contents_view, "path")
        # handle Apply tab operation button
        elif active_tab_id == TabName.apply_tab.name:
            current_view_id = self.query_one(
                Id.apply.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            current_view = self.query_one(f"#{current_view_id}")
            current_path = getattr(current_view, "path")
        # handle Re-Add tab operation button
        elif active_tab_id == TabName.re_add_tab.name:
            current_view_id = self.query_one(
                Id.re_add.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            current_view = self.query_one(f"#{current_view_id}")
            current_path = getattr(current_view, "path")

        if tab_ids is None:
            self.notify("Cannot push the operate screen", severity="error")
            return

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
