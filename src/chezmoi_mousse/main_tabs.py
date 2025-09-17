from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalGroup
from textual.widgets import (
    Button,
    Collapsible,
    ContentSwitcher,
    DataTable,
    Input,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
    Switch,
)

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.chezmoi import (
    CHEZMOI_COMMAND_FOUND,
    app_log,
    chezmoi,
    init_log,
    output_log,
)
from chezmoi_mousse.constants import (
    FLOW,
    BorderTitle,
    DoctorCollapsibles,
    TcssStr,
)
from chezmoi_mousse.containers import (
    ButtonsHorizontal,
    ButtonsVertical,
    InitCloneRepo,
    InitPurgeRepo,
    OperateTabsBase,
    SwitchSlider,
    TreeContentSwitcher,
)
from chezmoi_mousse.id_typing import (
    Area,
    Id,
    NavBtn,
    OperateBtn,
    PwMgrInfo,
    Switches,
    TabBtn,
    TreeName,
    ViewName,
)
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    FilteredDirTree,
    GitLogView,
)


class ApplyTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.apply)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=Id.apply.tab_vertical_id(area=Area.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                tab_ids=Id.apply,
                buttons=(TabBtn.tree, TabBtn.list),
                area=Area.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.apply)

        with Vertical(
            id=Id.apply.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
        ):
            yield ButtonsHorizontal(
                tab_ids=Id.apply,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=Area.right,
            )
            with ContentSwitcher(
                id=Id.apply.content_switcher_id(area=Area.right),
                initial=Id.apply.view_id(view=ViewName.diff_view),
            ):
                yield DiffView(ids=Id.apply, reverse=False)
                yield ContentsView(ids=Id.apply)
                yield GitLogView(ids=Id.apply)

        yield SwitchSlider(
            tab_ids=Id.apply,
            switches=(Switches.unchanged, Switches.expand_all),
        )

    def on_mount(self) -> None:
        self.query_one(
            Id.apply.content_switcher_id("#", area=Area.right), ContentSwitcher
        ).add_class(TcssStr.content_switcher_right, TcssStr.border_title_top)
        self.disable_buttons(
            (
                OperateBtn.apply_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
        )


class ReAddTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.re_add)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=Id.re_add.tab_vertical_id(area=Area.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                tab_ids=Id.re_add,
                buttons=(TabBtn.tree, TabBtn.list),
                area=Area.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.re_add)

        with Vertical(id=Id.re_add.tab_vertical_id(area=Area.right)):
            yield ButtonsHorizontal(
                tab_ids=Id.re_add,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
                area=Area.right,
            )

            with ContentSwitcher(
                id=Id.re_add.content_switcher_id(area=Area.right),
                initial=Id.re_add.view_id(view=ViewName.diff_view),
            ):
                yield DiffView(ids=Id.re_add, reverse=True)
                yield ContentsView(ids=Id.re_add)
                yield GitLogView(ids=Id.re_add)

        yield SwitchSlider(
            tab_ids=Id.re_add,
            switches=(Switches.unchanged, Switches.expand_all),
        )

    def on_mount(self) -> None:
        self.query_one(
            Id.re_add.tab_vertical_id("#", area=Area.right), Vertical
        ).add_class(TcssStr.tab_right_vertical)
        self.query_one(
            Id.re_add.content_switcher_id("#", area=Area.right),
            ContentSwitcher,
        ).add_class(TcssStr.content_switcher_right, TcssStr.border_title_top)
        self.disable_buttons(
            (
                OperateBtn.re_add_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
        )


class AddTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.add)

    def compose(self) -> ComposeResult:
        with VerticalGroup(id=Id.add.tab_vertical_id(area=Area.left)):
            yield FilteredDirTree(
                chezmoi.destDir,
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
        contents_view.border_title = str(chezmoi.destDir)
        contents_view.add_class(TcssStr.border_title_top)
        left_side = self.query_one(
            Id.add.tab_vertical_id("#", area=Area.left), VerticalGroup
        )
        left_side.border_title = str(chezmoi.destDir)
        left_side.add_class(
            TcssStr.tab_left_vertical, TcssStr.border_title_top
        )

        tree = self.query_one(
            Id.add.tree_id("#", tree=TreeName.add_tree), FilteredDirTree
        )
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
            f"{event.node.data.path.relative_to(chezmoi.destDir)}"
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
            f"{event.node.data.path.relative_to(chezmoi.destDir)}"
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


class InitTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.init)
        self.repo_url: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield ButtonsHorizontal(
                tab_ids=Id.init,
                buttons=(
                    TabBtn.clone_repo,
                    TabBtn.new_repo,
                    TabBtn.purge_repo,
                ),
                area=Area.top,
            )
            with ContentSwitcher(
                id=Id.init.content_switcher_id(area=Area.top),
                initial=Id.init.view_id(view=ViewName.init_clone_view),
                classes=TcssStr.border_title_top,
            ):
                yield InitCloneRepo()
                with Vertical(id=Id.init.view_id(view=ViewName.init_new_view)):
                    yield Label("Initialize a new chezmoi git repository")
                    yield Input(placeholder="Enter config file path")
                    yield ButtonsHorizontal(
                        tab_ids=Id.init,
                        buttons=(OperateBtn.new_repo,),
                        area=Area.bottom,
                    )
                yield InitPurgeRepo()

        yield SwitchSlider(
            tab_ids=Id.init,
            switches=(Switches.guess_url, Switches.clone_and_apply),
        )

    def on_mount(self) -> None:
        init_log.log_success("Ready to run chezmoi commands.")

    @on(Button.Pressed, ".operate_button")
    def handle_operation_button(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == Id.init.button_id(btn=OperateBtn.clone_repo):
            chezmoi.perform.init_clone_repo(str(self.repo_url))
            self.query_one(
                self.tab_ids.button_id("#", btn=OperateBtn.clone_repo), Button
            ).disabled = True
        elif event.button.id == Id.init.button_id(btn=OperateBtn.new_repo):
            chezmoi.perform.init_new_repo()
            self.query_one(
                self.tab_ids.button_id("#", btn=OperateBtn.new_repo), Button
            ).disabled = True
        elif event.button.id == Id.init.button_id(btn=OperateBtn.purge_repo):
            chezmoi.perform.purge()
            self.query_one(
                self.tab_ids.button_id("#", btn=OperateBtn.purge_repo), Button
            ).disabled = True


class ConfigTab(Horizontal):

    def __init__(self) -> None:
        super().__init__(id=Id.config.tab_container_id)

    def compose(self) -> ComposeResult:

        with VerticalGroup(
            id=Id.config.tab_vertical_id(area=Area.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsVertical(
                tab_ids=Id.config,
                buttons=(
                    NavBtn.cat_config,
                    NavBtn.ignored,
                    NavBtn.template_data,
                    NavBtn.diagram,
                ),
                area=Area.left,
            )

        with Vertical(
            id=Id.config.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
        ):
            with ContentSwitcher(
                id=Id.config.content_switcher_id(area=Area.right),
                initial=Id.config.view_id(view=ViewName.cat_config),
            ):
                yield Vertical(
                    Label('"chezmoi cat-config" output'),
                    Pretty(chezmoi.run.cat_config()),
                    id=Id.config.view_id(view=ViewName.cat_config),
                )
                yield Vertical(
                    Label('"chezmoi ignored" output'),
                    Pretty(chezmoi.run.ignored()),
                    id=Id.config.view_id(view=ViewName.config_ignored),
                )
                yield Vertical(
                    Label('"chezmoi data" output'),
                    Pretty(chezmoi.run.template_data()),
                    id=Id.config.view_id(view=ViewName.template_data),
                )
                yield Vertical(
                    Label("chezmoi diagram"),
                    Static(FLOW, classes=TcssStr.flow_diagram),
                    id=Id.config.view_id(view=ViewName.diagram),
                )

    def on_mount(self) -> None:
        self.query(Label).add_class(TcssStr.config_tab_label)
        self.query_exactly_one(ContentSwitcher).add_class(
            TcssStr.content_switcher_right
        )

    @on(Button.Pressed, ".navigate_button")
    def update_contents(self, event: Button.Pressed) -> None:
        event.stop()
        content_switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.id == Id.config.button_id(btn=(NavBtn.cat_config)):
            content_switcher.current = Id.config.view_id(
                view=ViewName.cat_config
            )
        elif event.button.id == Id.config.button_id(btn=NavBtn.ignored):
            content_switcher.current = Id.config.view_id(
                view=ViewName.config_ignored
            )
        elif event.button.id == Id.config.button_id(btn=NavBtn.template_data):
            content_switcher.current = Id.config.view_id(
                view=ViewName.template_data
            )
        elif event.button.id == Id.config.button_id(btn=NavBtn.diagram):
            content_switcher.current = Id.config.view_id(view=ViewName.diagram)


class DoctorTab(Vertical):

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
            yield ButtonsHorizontal(
                tab_ids=Id.doctor,
                buttons=(OperateBtn.refresh_doctor_data,),
                area=Area.bottom,
            )

            yield Collapsible(
                ListView(id=DoctorCollapsibles.pw_mgr_info.name),
                title=DoctorCollapsibles.pw_mgr_info,
            )

    @on(
        Button.Pressed,
        Id.doctor.button_id("#", btn=OperateBtn.refresh_doctor_data),
    )
    def on_refresh_doctor_data(self, event: Button.Pressed) -> None:
        if not CHEZMOI_COMMAND_FOUND:
            self.notify(
                "The chezmoi command is not available", severity="error"
            )
        chezmoi.doctor.update()
        self.query_one(DataTable[Text]).clear()
        self.populate_doctor_data()
        self.notify("Doctor data refreshed")

    def populate_doctor_data(self) -> None:
        if not CHEZMOI_COMMAND_FOUND:
            self.notify(
                "The chezmoi command is not available", severity="error"
            )
        if not chezmoi.doctor.list_out:
            return
        doctor_table: DataTable[Text] = self.query_one(DataTable[Text])
        doctor_data = chezmoi.doctor.list_out
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


class LogsTab(Container):

    def __init__(self) -> None:
        super().__init__(id=Id.logs.tab_container_id)

    def compose(self) -> ComposeResult:

        yield ButtonsHorizontal(
            tab_ids=Id.logs,
            buttons=(TabBtn.app_log, TabBtn.output_log),
            area=Area.top,
        )
        with ContentSwitcher(
            id=Id.logs.content_switcher_id(area=Area.top),
            initial=Id.logs.view_id(view=ViewName.app_log_view),
            classes=TcssStr.border_title_top,
        ):
            yield app_log
            yield output_log

    def on_mount(self) -> None:
        self.query_exactly_one(ContentSwitcher).border_title = (
            BorderTitle.app_log
        )
