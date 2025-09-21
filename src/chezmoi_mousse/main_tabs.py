from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Input,
    Label,
    Link,
    ListItem,
    ListView,
    Static,
    Switch,
)

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.button_groups import ButtonsVertical
from chezmoi_mousse.constants import (
    Area,
    OperateBtn,
    TabBtn,
    TcssStr,
    TreeName,
    ViewName,
)
from chezmoi_mousse.containers import OperateTabsBase, SwitchSlider
from chezmoi_mousse.content_switchers import (
    ConfigTabSwitcher,
    InitTabSwitcher,
    LogsTabSwitcher,
    TreeSwitcher,
    ViewSwitcher,
)
from chezmoi_mousse.id_typing import AppType, Id, PwMgrInfo, Switches
from chezmoi_mousse.messages import InvalidInputMessage
from chezmoi_mousse.widgets import ContentsView, FilteredDirTree


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
        with VerticalGroup(id=Id.add.tab_vertical_id(area=Area.left)):
            # Will set path in on_mount when app is available
            yield FilteredDirTree(
                Path(),
                id=Id.add.tree_id(tree=TreeName.add_tree),
                classes=TcssStr.dir_tree_widget,
            )
        with Vertical(id=Id.add.tab_vertical_id(area=Area.right)):
            yield ContentsView(ids=Id.add)

        yield SwitchSlider(
            tab_ids=Id.add,
            switches=(Switches.unmanaged_dirs, Switches.unwanted),
        )

    def on_mount(self) -> None:
        contents_view = self.query_one(
            Id.add.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.border_title = str(self.app.destDir)
        contents_view.add_class(TcssStr.border_title_top)
        left_side = self.query_one(
            Id.add.tab_vertical_id("#", area=Area.left), VerticalGroup
        )
        left_side.border_title = str(self.app.destDir)
        left_side.add_class(
            TcssStr.tab_left_vertical, TcssStr.border_title_top
        )

        tree = self.query_one(
            Id.add.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        tree.path = self.app.destDir
        tree.show_root = False
        tree.guide_depth = 3
        self.disable_buttons((OperateBtn.add_file, OperateBtn.add_dir))

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
            f"{event.node.data.path.relative_to(self.app.destDir)}"
        )
        self.enable_buttons((OperateBtn.add_file,))

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        contents_view = self.query_one(
            Id.add.view_id("#", view=ViewName.contents_view), ContentsView
        )
        contents_view.path = event.node.data.path
        contents_view.border_title = (
            f"{event.node.data.path.relative_to(self.app.destDir)}"
        )
        self.disable_buttons((OperateBtn.add_file,))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            Id.add.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
        if event.switch.id == Id.add.switch_id(switch=Switches.unmanaged_dirs):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == Id.add.switch_id(switch=Switches.unwanted):
            tree.unwanted = event.value
        tree.reload()


class InitTab(Vertical, AppType):

    def __init__(self) -> None:
        super().__init__(id=Id.init.tab_container_id)
        self.repo_url: str | None = None

    def compose(self) -> ComposeResult:
        yield InitTabSwitcher(tab_ids=Id.init)
        yield self.app.chezmoi.init_log
        yield SwitchSlider(
            tab_ids=Id.init,
            switches=(Switches.guess_url, Switches.clone_and_apply),
        )

    def on_mount(self) -> None:
        self.query(Label).add_class(TcssStr.config_tab_label)
        self.app.chezmoi.init_log.success("Ready to run chezmoi commands.")
        self.query_exactly_one(ButtonsVertical).add_class(
            TcssStr.tab_left_vertical
        )

    @on(Input.Submitted)
    def show_invalid_reasons(self, event: Input.Submitted) -> None:
        if (
            event.validation_result is not None
            and not event.validation_result.is_valid
        ):
            self.post_message(
                InvalidInputMessage(
                    reasons=event.validation_result.failure_descriptions
                )
            )

    @on(Button.Pressed, ".operate_button")
    def handle_operation_button(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == Id.init.button_id(btn=OperateBtn.clone_repo):
            self.app.chezmoi.perform.init_clone_repo(str(self.repo_url))
            self.query_one(
                Id.init.button_id("#", btn=OperateBtn.clone_repo), Button
            ).disabled = True
        elif event.button.id == Id.init.button_id(btn=OperateBtn.new_repo):
            self.app.chezmoi.perform.init_new_repo()
            self.query_one(
                Id.init.button_id("#", btn=OperateBtn.new_repo), Button
            ).disabled = True
        elif event.button.id == Id.init.button_id(btn=OperateBtn.purge_repo):
            self.app.chezmoi.perform.purge()
            self.query_one(
                Id.init.button_id("#", btn=OperateBtn.purge_repo), Button
            ).disabled = True

    def action_toggle_switch_slider(self) -> None:
        self.query_one(
            Id.init.switches_slider_qid, VerticalGroup
        ).toggle_class("-visible")


class ConfigTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__(id=Id.config.tab_container_id)

    def compose(self) -> ComposeResult:
        yield ConfigTabSwitcher(Id.config)

    def on_mount(self) -> None:
        self.query(Label).add_class(TcssStr.config_tab_label)


class DoctorTab(Vertical, AppType):

    def __init__(self) -> None:
        super().__init__(
            id=Id.doctor.tab_container_id, classes=TcssStr.doctor_vertical
        )
        self.dr_style = {
            "ok": theme.vars["text-success"],
            "info": theme.vars["foreground-darken-1"],
            "warning": theme.vars["text-warning"],
            "failed": theme.vars["text-error"],
            "error": theme.vars["text-error"],
        }

    def compose(self) -> ComposeResult:
        yield DataTable[Text](id=Id.doctor.datatable_id(), show_cursor=False)
        with VerticalGroup(classes=TcssStr.doctor_vertical_group):

            yield Collapsible(
                ListView(), title="Password managers not found in $PATH"
            )

    def populate_doctor_data(self) -> None:

        doctor_table: DataTable[Text] = self.query_one(DataTable[Text])
        doctor_data = self.app.chezmoi.doctor.list_out
        if not doctor_table.columns:
            doctor_table.add_columns(*doctor_data[0].split())

        for line in doctor_data[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                self.populate_pw_mgr_info_collapsible(row[1])
                new_row = [
                    Text(cell_text, style=self.dr_style["info"])
                    for cell_text in row
                ]
                doctor_table.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.dr_style[row[0]]}")
                    for cell_text in row
                ]
                doctor_table.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                self.populate_pw_mgr_info_collapsible(row[1])
                new_row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                doctor_table.add_row(*new_row)
            else:
                row = [Text(cell_text) for cell_text in row]
                doctor_table.add_row(*row)

    def populate_pw_mgr_info_collapsible(self, row_var: str) -> None:
        list_view = self.query_exactly_one(ListView)
        for pw_mgr in PwMgrInfo:
            if pw_mgr.value.doctor_check == row_var:
                list_view.append(
                    ListItem(
                        Link(row_var, url=pw_mgr.value.link),
                        Static(pw_mgr.value.description),
                    )
                )
                break


class LogsTab(Vertical, AppType):

    def __init__(self) -> None:
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        super().__init__(id=Id.logs.tab_container_id)

    def compose(self) -> ComposeResult:
        yield LogsTabSwitcher(tab_ids=Id.logs)
