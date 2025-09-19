from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.validation import URL
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
    Select,
    Static,
    Switch,
)

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.constants import FLOW, BorderTitle, TcssStr
from chezmoi_mousse.containers import (
    ButtonsVertical,
    OperateBtnHorizontal,
    OperateTabsBase,
    SwitchSlider,
    TabBtnHorizontal,
    TreeContentSwitcher,
)
from chezmoi_mousse.id_typing import (
    AppType,
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
from chezmoi_mousse.messages import InvalidInputMessage
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
            yield TabBtnHorizontal(
                tab_ids=Id.apply,
                buttons=(TabBtn.tree, TabBtn.list),
                area=Area.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.apply)

        with Vertical(
            id=Id.apply.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
        ):
            yield TabBtnHorizontal(
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
            yield TabBtnHorizontal(
                tab_ids=Id.re_add,
                buttons=(TabBtn.tree, TabBtn.list),
                area=Area.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.re_add)

        with Vertical(id=Id.re_add.tab_vertical_id(area=Area.right)):
            yield TabBtnHorizontal(
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


class AddTab(OperateTabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.add)

    def compose(self) -> ComposeResult:
        with VerticalGroup(id=Id.add.tab_vertical_id(area=Area.left)):
            yield FilteredDirTree(
                self.app.destDir,
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
        with Horizontal():
            yield ButtonsVertical(
                tab_ids=Id.init,
                buttons=(
                    NavBtn.new_repo,
                    NavBtn.clone_repo,
                    NavBtn.purge_repo,
                ),
                area=Area.left,
            )
            with Vertical(
                id=Id.init.tab_vertical_id(area=Area.right),
                classes=TcssStr.tab_right_vertical,
            ):
                with ContentSwitcher(
                    id=Id.init.content_switcher_id(area=Area.right),
                    initial=Id.init.view_id(view=ViewName.init_new_view),
                    classes=TcssStr.content_switcher_right,
                ):
                    # New Repo Content
                    yield Vertical(
                        Label("Initialize new chezmoi git repository"),
                        Input(placeholder="Enter config file path"),
                        OperateBtnHorizontal(
                            tab_ids=Id.init, buttons=(OperateBtn.new_repo,)
                        ),
                        id=Id.init.view_id(view=ViewName.init_new_view),
                    )
                    # Clone Repo Content
                    yield Vertical(
                        Label("Clone existing chezmoi git repository"),
                        # TODO: implement guess feature from chezmoi
                        # TODO: add selection for https(with PAT token) or ssh
                        HorizontalGroup(
                            Vertical(
                                Select[str].from_values(
                                    ["https", "ssh"],
                                    classes=TcssStr.input_select,
                                    value="https",
                                    allow_blank=False,
                                    type_to_search=False,
                                ),
                                classes=TcssStr.input_select_vertical,
                            ),
                            Vertical(
                                Input(
                                    placeholder="Enter repository URL",
                                    validate_on=["submitted"],
                                    validators=URL(),
                                    classes=TcssStr.input_field,
                                ),
                                classes=TcssStr.input_field_vertical,
                            ),
                        ),
                        OperateBtnHorizontal(
                            tab_ids=Id.init, buttons=(OperateBtn.clone_repo,)
                        ),
                        id=Id.init.view_id(view=ViewName.init_clone_view),
                    )
                    # Purge chezmoi repo
                    yield Vertical(
                        Label("Purge current chezmoi git repository"),
                        Static(
                            "Remove chezmoi's configuration, state, and source directory, but leave the target state intact."
                        ),
                        OperateBtnHorizontal(
                            tab_ids=Id.init, buttons=(OperateBtn.purge_repo,)
                        ),
                        id=Id.init.view_id(view=ViewName.init_purge_view),
                    )
            yield SwitchSlider(
                tab_ids=Id.init,
                switches=(Switches.guess_url, Switches.clone_and_apply),
            )
        yield self.app.chezmoi.init_log

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
            self.app.post_message(
                InvalidInputMessage(
                    reasons=event.validation_result.failure_descriptions
                )
            )

    @on(Button.Pressed, ".navigate_button")
    def handle_navigation_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        # Init Content Switcher
        if event.button.id == Id.init.button_id(btn=NavBtn.new_repo):
            self.query_one(
                Id.init.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current = Id.init.view_id(view=ViewName.init_new_view)
        elif event.button.id == Id.init.button_id(btn=NavBtn.clone_repo):
            self.query_one(
                Id.init.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current = Id.init.view_id(view=ViewName.init_clone_view)
        elif event.button.id == Id.init.button_id(btn=NavBtn.purge_repo):
            self.query_one(
                Id.init.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current = Id.init.view_id(view=ViewName.init_purge_view)

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
            # TODO: make sure scrollbars appear when there's overflow
            with ContentSwitcher(
                id=Id.config.content_switcher_id(area=Area.right),
                initial=Id.config.view_id(view=ViewName.cat_config),
            ):
                yield Vertical(
                    Label('"chezmoi cat-config" output'),
                    Pretty(self.app.chezmoi.run.cat_config()),
                    id=Id.config.view_id(view=ViewName.cat_config),
                )
                yield Vertical(
                    Label('"chezmoi ignored" output'),
                    Pretty(self.app.chezmoi.run.ignored()),
                    id=Id.config.view_id(view=ViewName.config_ignored),
                )
                yield Vertical(
                    Label('"chezmoi data" output'),
                    Pretty(self.app.chezmoi.run.template_data()),
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


class LogsTab(Container, AppType):

    # TODO: implement maximized key binding

    def __init__(self) -> None:
        super().__init__(id=Id.logs.tab_container_id)
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        if self.app.chezmoi.app_cfg.dev_mode:
            self.tab_buttons += (TabBtn.debug_log,)

    def compose(self) -> ComposeResult:

        yield TabBtnHorizontal(
            tab_ids=Id.logs, buttons=self.tab_buttons, area=Area.top
        )
        with ContentSwitcher(
            id=Id.logs.content_switcher_id(area=Area.top),
            initial=Id.logs.view_id(view=ViewName.app_log_view),
            classes=TcssStr.border_title_top,
        ):
            yield self.app.chezmoi.app_log
            yield self.app.chezmoi.output_log
            if self.app.chezmoi.app_cfg.dev_mode:
                yield self.app.chezmoi.debug_log

    def on_mount(self) -> None:
        self.query_exactly_one(ContentSwitcher).border_title = (
            BorderTitle.app_log
        )

    @on(Button.Pressed, ".tab_button")
    def handle_logs_tab_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        # AppLog/OutputLog/DebugLog Content Switcher
        if event.button.id == Id.logs.button_id(btn=TabBtn.app_log):
            content_switcher = self.query_one(
                Id.logs.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            )
            content_switcher.current = Id.logs.view_id(
                view=ViewName.app_log_view
            )
            content_switcher.border_title = BorderTitle.app_log
        elif event.button.id == Id.logs.button_id(btn=TabBtn.output_log):
            content_switcher = self.query_one(
                Id.logs.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            )
            content_switcher.current = Id.logs.view_id(
                view=ViewName.output_log_view
            )
            content_switcher.border_title = BorderTitle.output_log
        elif (
            self.app.chezmoi.app_cfg.dev_mode
            and event.button.id == Id.logs.button_id(btn=TabBtn.debug_log)
        ):
            content_switcher = self.query_one(
                Id.logs.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            )
            content_switcher.current = Id.logs.view_id(
                view=ViewName.debug_log_view
            )
            content_switcher.border_title = BorderTitle.debug_log
