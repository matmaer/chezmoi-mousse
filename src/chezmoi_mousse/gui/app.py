from dataclasses import dataclass
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

from chezmoi_mousse import (
    Area,
    Chars,
    Id,
    LogName,
    OperateBtn,
    OperateHelp,
    PaneBtn,
    TabIds,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.gui import SplashReturnData
from chezmoi_mousse.gui.button_groups import OperateBtnHorizontal
from chezmoi_mousse.gui.chezmoi import Chezmoi
from chezmoi_mousse.gui.directory_tree import FilteredDirTree
from chezmoi_mousse.gui.main_tabs import (
    AddTab,
    ApplyTab,
    ConfigTab,
    HelpTab,
    InitTab,
    LogsTab,
    ReAddTab,
)
from chezmoi_mousse.gui.overrides import CustomScrollBarRender
from chezmoi_mousse.gui.rich_logs import (
    AppLog,
    ContentsView,
    DebugLog,
    OutputLog,
)
from chezmoi_mousse.gui.screens import InstallHelp, Maximized, Operate
from chezmoi_mousse.gui.splash import LoadingScreen
from chezmoi_mousse.gui.widgets import (
    DoctorListView,
    DoctorTable,
    ExpandedTree,
    FlatTree,
    ManagedTree,
)

__all__ = ["ChezmoiGUI", "PreRunData"]

# TODO: implement 'chezmoi verify', if exit 0, display message in Tree
# widgets inform the user why the Tree widget is empty
# TODO: implement spinner for commands taking a bit longer like operations


@dataclass
class PreRunData:
    chezmoi_instance: Chezmoi
    changes_enabled: bool
    chezmoi_found: bool
    chezmoi_mousse_dark: Theme
    chezmoi_mousse_light: Theme
    custom_theme_vars: dict[str, str]
    dev_mode: bool
    home_dir: Path
    temp_dir: Path


class ChezmoiGUI(App[None]):
    def __init__(self, pre_run_data: PreRunData) -> None:

        self.chezmoi = pre_run_data.chezmoi_instance
        self.changes_enabled = pre_run_data.changes_enabled
        self.chezmoi_found = pre_run_data.chezmoi_found
        self.chezmoi_mousse_dark = pre_run_data.chezmoi_mousse_dark
        self.chezmoi_mousse_light = pre_run_data.chezmoi_mousse_light
        self.custom_theme_vars = pre_run_data.custom_theme_vars
        self.destDir: Path = pre_run_data.home_dir
        self.dev_mode = pre_run_data.dev_mode
        self.sourceDir: Path = pre_run_data.temp_dir

        self.app_log: AppLog
        self.output_log: OutputLog
        self.debug_log: DebugLog

        self.git_autoadd: bool = False
        self.git_autocommit: bool = False
        self.git_autopush: bool = False

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
            with TabPane(PaneBtn.apply_tab.value, id=PaneBtn.apply_tab.name):
                yield ApplyTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.apply,
                    buttons=(
                        OperateBtn.apply_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(PaneBtn.re_add_tab.value, id=PaneBtn.re_add_tab.name):
                yield ReAddTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.re_add,
                    buttons=(
                        OperateBtn.re_add_file,
                        OperateBtn.forget_file,
                        OperateBtn.destroy_file,
                    ),
                )
            with TabPane(PaneBtn.add_tab.value, id=PaneBtn.add_tab.name):
                yield AddTab()
                yield OperateBtnHorizontal(
                    tab_ids=Id.add,
                    buttons=(OperateBtn.add_file, OperateBtn.add_dir),
                )
            with TabPane(PaneBtn.init_tab.value, id=PaneBtn.init_tab.name):
                yield InitTab()
            with TabPane(PaneBtn.logs_tab.value, id=PaneBtn.logs_tab.name):
                yield LogsTab()
            with TabPane(PaneBtn.config_tab.value, id=PaneBtn.config_tab.name):
                yield ConfigTab()
            with TabPane(PaneBtn.help_tab.value, id=PaneBtn.help_tab.name):
                yield HelpTab()
        yield Footer()

    def on_mount(self) -> None:
        app_logger = self.query_one(f"#{LogName.app_log.name}", AppLog)
        self.app_log = app_logger
        self.chezmoi.app_log = app_logger

        output_logger = self.query_one(
            f"#{LogName.output_log.name}", OutputLog
        )
        self.output_log = output_logger
        self.chezmoi.output_log = output_logger

        if self.dev_mode is True:
            debug_logger = self.query_one(
                f"#{LogName.debug_log.name}", DebugLog
            )
            self.debug_log = debug_logger
            self.chezmoi.debug_log = debug_logger

        self.register_theme(self.chezmoi_mousse_light)
        self.register_theme(self.chezmoi_mousse_dark)
        theme_name = "chezmoi-mousse-dark"
        self.theme = theme_name

        if self.chezmoi_found is False:
            self.push_screen(
                LoadingScreen(chezmoi_found=self.chezmoi_found),
                callback=self.run_post_splash_actions,
            )
            return
        # Only continue if chezmoi is found
        self.app_log.success("App initialized successfully")
        # TODO: inform user only file mode is supported if detected in the user config
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        self.title = "-  c h e z m o i  m o u s s e  -"

        self.app_log.success(f"Theme set to {theme_name}")
        self.app_log.success(f"chezmoi command found: {self.chezmoi_found}")
        self.app_log.ready_to_run("--- Start loading screen ---")
        self.push_screen(
            LoadingScreen(chezmoi_found=self.chezmoi_found),
            callback=self.run_post_splash_actions,
        )

    def run_post_splash_actions(
        self, return_data: SplashReturnData | None
    ) -> None:
        if return_data is None:
            self.push_screen(InstallHelp())
            return
        self.app_log.ready_to_run("--- Loading screen completed ---")
        # Populate Doctor DataTable
        pw_mgr_cmds: list[str] = self.query_one(
            Id.config.datatable_qid, DoctorTable
        ).populate_doctor_data(return_data.doctor.splitlines())
        self.query_one(
            Id.config.listview_qid, DoctorListView
        ).populate_listview(pw_mgr_cmds)

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
                ).populate_root_node()
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

        if active_tab_id == PaneBtn.apply_tab.name:
            active_widget_id = self.query_one(
                Id.apply.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            active_widget = self.query_one(f"#{active_widget_id}")
            current_path = getattr(active_widget, "path")
            id_to_maximize = active_widget.id
            tab_ids = getattr(Id, "apply")

        elif active_tab_id == PaneBtn.re_add_tab.name:
            # Determine what view to show in the screen
            active_widget_id = self.query_one(
                Id.re_add.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            active_widget = self.query_one(f"#{active_widget_id}")
            current_path = getattr(active_widget, "path")
            id_to_maximize = active_widget.id
            tab_ids = getattr(Id, "re_add")

        elif active_tab_id == PaneBtn.add_tab.name:
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
        if active_tab_id == PaneBtn.add_tab.name:
            add_tab_contents_view = self.query_one(
                Id.add.view_id("#", view=ViewName.contents_view), ContentsView
            )
            current_path = getattr(add_tab_contents_view, "path")
        # handle Apply tab operation button
        elif active_tab_id == PaneBtn.apply_tab.name:
            current_view_id = self.query_one(
                Id.apply.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current
            current_view = self.query_one(f"#{current_view_id}")
            current_path = getattr(current_view, "path")
        # handle Re-Add tab operation button
        elif active_tab_id == PaneBtn.re_add_tab.name:
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

    def on_theme_change(self, _: str, new_theme: str) -> None:
        # TODO: this should not be necessary anymore, use textual app attributes
        new_theme_object: Theme | None = self.get_theme(new_theme)
        assert isinstance(new_theme_object, Theme)
        self.custom_theme_vars = new_theme_object.to_color_system().generate()
        self.app_log.success(f"Theme set to {new_theme}")
