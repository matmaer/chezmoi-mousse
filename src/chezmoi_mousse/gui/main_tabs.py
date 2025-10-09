from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.lazy import Lazy
from textual.widgets import Button, Input, Switch

from chezmoi_mousse import (
    AreaName,
    ChangeCmd,
    Id,
    LogName,
    NavBtn,
    OperateBtn,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.button_groups import (
    NavButtonsVertical,
    TabBtnHorizontal,
)
from chezmoi_mousse.gui.containers import OperateTabsBase, SwitchSlider
from chezmoi_mousse.gui.content_switchers import (
    ConfigTabSwitcher,
    HelpTabSwitcher,
    InitTabSwitcher,
    LogsTabSwitcher,
    TreeSwitcher,
    ViewSwitcher,
)
from chezmoi_mousse.gui.directory_tree import FilteredDirTree
from chezmoi_mousse.gui.rich_logs import ContentsView

__all__ = [
    "AddTab",
    "ApplyTab",
    "ConfigTab",
    "HelpTab",
    "InitTab",
    "LogsTab",
    "ReAddTab",
]


class ApplyTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.apply)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=Id.apply.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                tab_ids=self.tab_ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(tab_ids=Id.apply)
        with Vertical(id=Id.apply.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                tab_ids=Id.apply,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(tab_ids=Id.apply, diff_reverse=False)
        yield SwitchSlider(
            tab_ids=Id.apply,
            switches=(Switches.unchanged, Switches.expand_all),
        )


class ReAddTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.re_add)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=Id.re_add.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield TabBtnHorizontal(
                tab_ids=self.tab_ids,
                buttons=(TabBtn.tree, TabBtn.list),
                area=AreaName.left,
            )
            yield TreeSwitcher(tab_ids=Id.re_add)
        with Vertical(id=Id.re_add.tab_vertical_id(area=AreaName.right)):
            yield TabBtnHorizontal(
                tab_ids=Id.re_add,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=AreaName.right,
            )
            yield ViewSwitcher(tab_ids=Id.re_add, diff_reverse=True)
        yield SwitchSlider(
            tab_ids=Id.re_add,
            switches=(Switches.unchanged, Switches.expand_all),
        )


class AddTab(OperateTabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.add)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=Id.add.tab_vertical_id(area=AreaName.left),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield FilteredDirTree(
                Path.home(), id=Id.add.tree_id(tree=TreeName.add_tree)
            )
        with Vertical(id=Id.add.tab_vertical_id(area=AreaName.right)):
            yield ContentsView(tab_ids=Id.add)

        yield SwitchSlider(
            tab_ids=Id.add,
            switches=(Switches.unmanaged_dirs, Switches.unwanted),
        )

    def on_mount(self) -> None:
        contents_view = self.query_exactly_one(ContentsView)
        contents_view.add_class(Tcss.border_title_top.name)
        contents_view.border_title = str(self.app.destDir)

        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.add_class(
            Tcss.dir_tree_widget.name, Tcss.border_title_top.name
        )
        dir_tree.border_title = " destDir "
        dir_tree.show_root = False
        dir_tree.guide_depth = 3

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        contents_view = self.query_one(
            Id.add.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = (
            f" {event.node.data.path.relative_to(self.app.destDir)} "
        )

    @on(FilteredDirTree.DirectorySelected)
    def update_contents_view_and_title(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        contents_view = self.query_one(
            Id.add.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = (
            f" {event.node.data.path.relative_to(self.app.destDir)} "
        )

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            Id.add.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        if event.switch.id == Id.add.switch_id(
            switch=Switches.unmanaged_dirs.value
        ):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == Id.add.switch_id(
            switch=Switches.unwanted.value
        ):
            tree.unwanted = event.value
        tree.reload()


class InitTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__(id=Id.init.tab_container_id)
        self.repo_url: str | None = None

    def compose(self) -> ComposeResult:
        yield NavButtonsVertical(
            tab_ids=Id.init,
            buttons=(NavBtn.new_repo, NavBtn.clone_repo, NavBtn.purge_repo),
        )
        yield InitTabSwitcher(tab_ids=Id.init)

    @on(Input.Submitted)
    def log_invalid_reasons(self, event: Input.Submitted) -> None:
        if (
            event.validation_result is not None
            and not event.validation_result.is_valid
        ):
            text_lines: str = "\n".join(
                event.validation_result.failure_descriptions
            )
            self.app.notify(text_lines, severity="error")

    @on(Button.Pressed, Tcss.nav_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(InitTabSwitcher)
        if event.button.id == Id.init.button_id(btn=NavBtn.new_repo):
            switcher.current = Id.init.view_id(view=ViewName.init_new_view)
        elif event.button.id == Id.init.button_id(btn=NavBtn.clone_repo):
            switcher.current = Id.init.view_id(view=ViewName.init_clone_view)
        elif event.button.id == Id.init.button_id(btn=NavBtn.purge_repo):
            switcher.current = Id.init.view_id(view=ViewName.init_purge_view)

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operation_button(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == Id.init.button_id(btn=OperateBtn.clone_repo):
            self.app.chezmoi.perform(ChangeCmd.init, self.repo_url)
            self.query_one(
                Id.init.button_id("#", btn=OperateBtn.clone_repo), Button
            ).disabled = True
        elif event.button.id == Id.init.button_id(btn=OperateBtn.new_repo):
            self.app.chezmoi.perform(ChangeCmd.init)
            self.query_one(
                Id.init.button_id("#", btn=OperateBtn.new_repo), Button
            ).disabled = True
        elif event.button.id == Id.init.button_id(btn=OperateBtn.purge_repo):
            self.app.chezmoi.perform(ChangeCmd.purge)
            self.query_one(
                Id.init.button_id("#", btn=OperateBtn.purge_repo), Button
            ).disabled = True


class LogsTab(Vertical, AppType):

    def __init__(self) -> None:
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        super().__init__(id=Id.logs.tab_container_id)

    def compose(self) -> ComposeResult:
        tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        if self.app.dev_mode is False:
            tab_buttons += (TabBtn.debug_log,)

        yield TabBtnHorizontal(
            tab_ids=Id.logs, buttons=tab_buttons, area=AreaName.top
        )
        yield LogsTabSwitcher(tab_ids=Id.logs)

    @on(Button.Pressed, Tcss.tab_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(LogsTabSwitcher)

        if event.button.id == Id.logs.button_id(btn=TabBtn.app_log):
            switcher.current = LogName.app_log.name
            switcher.border_title = LogName.app_log.value
        elif event.button.id == Id.logs.button_id(btn=TabBtn.output_log):
            switcher.current = LogName.output_log.name
            switcher.border_title = LogName.output_log.value
        elif self.app.dev_mode and event.button.id == Id.logs.button_id(
            btn=TabBtn.debug_log
        ):
            switcher.current = LogName.debug_log.name
            switcher.border_title = LogName.debug_log.value


class ConfigTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__(id=Id.config.tab_container_id)

    def compose(self) -> ComposeResult:
        yield NavButtonsVertical(
            tab_ids=Id.config,
            buttons=(
                NavBtn.doctor,
                NavBtn.cat_config,
                NavBtn.ignored,
                NavBtn.template_data,
            ),
        )
        # mount lazily as the compose method includes subprocess calls
        yield Lazy(ConfigTabSwitcher(Id.config))

    @on(Button.Pressed, Tcss.nav_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(ConfigTabSwitcher)
        if event.button.id == Id.config.button_id(btn=(NavBtn.doctor)):
            switcher.current = Id.config.view_id(view=ViewName.doctor_view)
        elif event.button.id == Id.config.button_id(btn=(NavBtn.cat_config)):
            switcher.current = Id.config.view_id(view=ViewName.cat_config_view)
        elif event.button.id == Id.config.button_id(btn=NavBtn.ignored):
            switcher.current = Id.config.view_id(
                view=ViewName.git_ignored_view
            )
        elif event.button.id == Id.config.button_id(btn=NavBtn.template_data):
            switcher.current = Id.config.view_id(
                view=ViewName.template_data_view
            )


class HelpTab(Horizontal):

    def __init__(self) -> None:
        super().__init__(id=Id.help.tab_container_id)

    def compose(self) -> ComposeResult:
        yield NavButtonsVertical(tab_ids=Id.help, buttons=(NavBtn.diagram,))
        yield HelpTabSwitcher(tab_ids=Id.help)

    @on(Button.Pressed, Tcss.nav_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(HelpTabSwitcher)
        if event.button.id == Id.help.button_id(btn=NavBtn.diagram):
            switcher.current = Id.help.view_id(view=ViewName.diagram_view)
