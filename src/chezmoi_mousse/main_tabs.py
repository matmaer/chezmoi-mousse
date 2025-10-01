from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.widgets import Button, Input, Label, Switch

from chezmoi_mousse.button_groups import NavButtonsVertical
from chezmoi_mousse.chezmoi import ChangeCmd
from chezmoi_mousse.containers import OperateTabsBase, SwitchSlider
from chezmoi_mousse.content_switchers import (
    ConfigTabSwitcher,
    HelpTabSwitcher,
    InitTabSwitcher,
    LogsTabSwitcher,
    TreeSwitcher,
    ViewSwitcher,
)
from chezmoi_mousse.directory_tree import FilteredDirTree
from chezmoi_mousse.id_typing import (
    AppType,
    Area,
    Id,
    OperateBtn,
    Switches,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.widgets import ContentsView


class ApplyTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.apply)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(tab_ids=Id.apply)
        yield ViewSwitcher(tab_ids=Id.apply, diff_reverse=False)
        yield SwitchSlider(
            tab_ids=Id.apply,
            switches=(Switches.unchanged, Switches.expand_all),
        )


class ReAddTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.re_add)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(tab_ids=Id.re_add)
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
            id=Id.add.tab_vertical_id(area=Area.left),
            classes=Tcss.tab_left_vertical,
        ):
            yield FilteredDirTree(
                Path.home(), id=Id.add.tree_id(tree=TreeName.add_tree)
            )
        with Vertical(id=Id.add.tab_vertical_id(area=Area.right)):
            yield ContentsView(tab_ids=Id.add)

        yield SwitchSlider(
            tab_ids=Id.add,
            switches=(Switches.unmanaged_dirs, Switches.unwanted),
        )

    def on_mount(self) -> None:
        contents_view = self.query_exactly_one(ContentsView)
        contents_view.add_class(Tcss.border_title_top)
        contents_view.border_title = str(self.app.destDir)

        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.add_class(Tcss.dir_tree_widget, Tcss.border_title_top)
        dir_tree.border_title = str(self.app.destDir)
        dir_tree.path = self.app.destDir
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
        if event.switch.id == Id.add.switch_id(switch=Switches.unmanaged_dirs):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == Id.add.switch_id(switch=Switches.unwanted):
            tree.unwanted = event.value
        tree.reload()


class InitTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__(id=Id.init.tab_container_id)
        self.repo_url: str | None = None

    def compose(self) -> ComposeResult:
        yield InitTabSwitcher(tab_ids=Id.init)

    def on_mount(self) -> None:
        self.query(Label).add_class(Tcss.section_label)
        self.query_exactly_one(NavButtonsVertical).add_class(
            Tcss.tab_left_vertical
        )

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

    @on(Button.Pressed, f".{Tcss.operate_button}")
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

    def action_toggle_switch_slider(self) -> None:
        self.query_one(
            Id.init.switches_slider_qid, VerticalGroup
        ).toggle_class("-visible")


class LogsTab(Vertical, AppType):

    def __init__(self) -> None:
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        super().__init__(id=Id.logs.tab_container_id)

    def compose(self) -> ComposeResult:
        yield LogsTabSwitcher(tab_ids=Id.logs)


class ConfigTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__(id=Id.config.tab_container_id)

    def compose(self) -> ComposeResult:
        yield ConfigTabSwitcher(Id.config)

    def on_mount(self) -> None:
        self.query(Label).add_class(Tcss.section_label)


class HelpTab(Vertical):

    def __init__(self) -> None:
        super().__init__(id=Id.help.tab_container_id)

    def compose(self) -> ComposeResult:
        yield HelpTabSwitcher(tab_ids=Id.help)
