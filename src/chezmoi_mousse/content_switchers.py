import json

from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.validation import URL
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Label,
    Pretty,
    Select,
    Static,
)

from chezmoi_mousse.button_groups import (
    ButtonsVertical,
    OperateBtnHorizontal,
    TabBtnHorizontal,
)
from chezmoi_mousse.chezmoi import LogsEnum, ReadCmd
from chezmoi_mousse.constants import (
    FLOW,
    Area,
    NavBtn,
    OperateBtn,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.id_typing import AppType, TabIds
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
)


class TreeSwitcher(VerticalGroup, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        # updated by OperateTabsBase in on_switch_changed method
        self.expand_all_state: bool = False
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.left),
            classes=Tcss.tab_left_vertical,
        )

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(
            tab_ids=self.tab_ids,
            buttons=(TabBtn.tree, TabBtn.list),
            area=Area.left,
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.left),
            initial=self.tab_ids.tree_id(tree=TreeName.managed_tree),
        ):
            yield ManagedTree(tab_ids=self.tab_ids)
            yield FlatTree(tab_ids=self.tab_ids)
            yield ExpandedTree(tab_ids=self.tab_ids)

    def on_mount(self) -> None:
        self.border_title = str(self.app.destDir)
        self.query_exactly_one(ContentSwitcher).add_class(
            Tcss.content_switcher_left, Tcss.border_title_top
        )


class ViewSwitcher(Vertical, AppType):
    def __init__(self, *, tab_ids: TabIds, diff_reverse: bool):
        self.tab_ids = tab_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=Tcss.tab_right_vertical,
        )

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(
            tab_ids=self.tab_ids,
            buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
            area=Area.right,
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.diff_view),
            classes=Tcss.border_title_top,
        ):
            yield DiffView(tab_ids=self.tab_ids, reverse=self.reverse)
            yield ContentsView(tab_ids=self.tab_ids)
            yield GitLogView(tab_ids=self.tab_ids)


class InitTabSwitcher(Horizontal):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(id=self.tab_ids.tab_vertical_id(area=Area.right))

    def compose(self) -> ComposeResult:
        yield ButtonsVertical(
            tab_ids=self.tab_ids,
            buttons=(NavBtn.new_repo, NavBtn.clone_repo, NavBtn.purge_repo),
            area=Area.left,
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.init_new_view),
            classes=Tcss.nav_content_switcher,
        ):
            # New Repo Content
            yield Vertical(
                Label("Initialize new chezmoi git repository"),
                Input(placeholder="Enter config file path"),
                OperateBtnHorizontal(
                    tab_ids=self.tab_ids, buttons=(OperateBtn.new_repo,)
                ),
                id=self.tab_ids.view_id(view=ViewName.init_new_view),
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
                            classes=Tcss.input_select,
                            value="https",
                            allow_blank=False,
                            type_to_search=False,
                        ),
                        classes=Tcss.input_select_vertical,
                    ),
                    Vertical(
                        Input(
                            placeholder="Enter repository URL",
                            validate_on=["submitted"],
                            validators=URL(),
                            classes=Tcss.input_field,
                        ),
                        classes=Tcss.input_field_vertical,
                    ),
                ),
                OperateBtnHorizontal(
                    tab_ids=self.tab_ids, buttons=(OperateBtn.clone_repo,)
                ),
                id=self.tab_ids.view_id(view=ViewName.init_clone_view),
            )
            # Purge chezmoi repo
            yield Vertical(
                Label("Purge current chezmoi git repository"),
                Static(
                    "Remove chezmoi's configuration, state, and source directory, but leave the target state intact."
                ),
                OperateBtnHorizontal(
                    tab_ids=self.tab_ids, buttons=(OperateBtn.purge_repo,)
                ),
                id=self.tab_ids.view_id(view=ViewName.init_purge_view),
            )

    @on(Button.Pressed, f".{Tcss.nav_button}")
    def switch_content(self, event: Button.Pressed) -> None:
        switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.id == self.tab_ids.button_id(btn=NavBtn.new_repo):
            switcher.current = self.tab_ids.view_id(
                view=ViewName.init_new_view
            )
        elif event.button.id == self.tab_ids.button_id(btn=NavBtn.clone_repo):
            switcher.current = self.tab_ids.view_id(
                view=ViewName.init_clone_view
            )
        elif event.button.id == self.tab_ids.button_id(btn=NavBtn.purge_repo):
            switcher.current = self.tab_ids.view_id(
                view=ViewName.init_purge_view
            )


class ConfigTabSwitcher(Horizontal, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=Tcss.tab_right_vertical,
        )

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_ids.tab_vertical_id(area=Area.left),
            classes=Tcss.tab_left_vertical,
        ):
            yield ButtonsVertical(
                tab_ids=self.tab_ids,
                buttons=(
                    NavBtn.cat_config,
                    NavBtn.ignored,
                    NavBtn.template_data,
                    NavBtn.diagram,
                ),
                area=Area.left,
            )

        with Vertical(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=Tcss.tab_right_vertical,
        ):
            # TODO: make sure scrollbars appear when there's overflow
            with ContentSwitcher(
                id=self.tab_ids.content_switcher_id(area=Area.right),
                initial=self.tab_ids.view_id(view=ViewName.cat_config),
                classes=Tcss.nav_content_switcher,
            ):
                yield Vertical(
                    Label('"chezmoi cat-config" output'),
                    Pretty(
                        self.app.chezmoi.read(ReadCmd.cat_config).splitlines()
                    ),
                    id=self.tab_ids.view_id(view=ViewName.cat_config),
                )
                yield Vertical(
                    Label('"chezmoi ignored" output'),
                    Pretty(
                        self.app.chezmoi.read(ReadCmd.ignored).splitlines()
                    ),
                    id=self.tab_ids.view_id(view=ViewName.config_ignored),
                )
                yield Vertical(
                    Label('"chezmoi data" output'),
                    Pretty(json.loads(self.app.chezmoi.read(ReadCmd.data))),
                    id=self.tab_ids.view_id(view=ViewName.template_data),
                )
                yield Vertical(
                    Label("chezmoi diagram"),
                    Static(FLOW, classes=Tcss.flow_diagram),
                    id=self.tab_ids.view_id(view=ViewName.diagram),
                )

    @on(Button.Pressed, f".{Tcss.nav_button}")
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(ContentSwitcher)
        if event.button.id == self.tab_ids.button_id(btn=(NavBtn.cat_config)):
            switcher.current = self.tab_ids.view_id(view=ViewName.cat_config)
        elif event.button.id == self.tab_ids.button_id(btn=NavBtn.ignored):
            switcher.current = self.tab_ids.view_id(
                view=ViewName.config_ignored
            )
        elif event.button.id == self.tab_ids.button_id(
            btn=NavBtn.template_data
        ):
            switcher.current = self.tab_ids.view_id(
                view=ViewName.template_data
            )
        elif event.button.id == self.tab_ids.button_id(btn=NavBtn.diagram):
            switcher.current = self.tab_ids.view_id(view=ViewName.diagram)


class LogsTabSwitcher(Vertical, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__()

    def compose(self) -> ComposeResult:
        tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        if self.app.chezmoi.init_cfg.dev_mode:
            tab_buttons += (TabBtn.debug_log,)

        yield TabBtnHorizontal(
            tab_ids=self.tab_ids, buttons=tab_buttons, area=Area.top
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.top),
            initial=self.tab_ids.view_id(view=ViewName.app_log_view),
            classes=Tcss.border_title_top,
        ):
            yield self.app.chezmoi.app_log
            yield self.app.chezmoi.output_log
            if self.app.chezmoi.init_cfg.dev_mode:
                yield self.app.chezmoi.debug_log

    @on(Button.Pressed, f".{Tcss.tab_button}")
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(ContentSwitcher)

        if event.button.id == self.tab_ids.button_id(btn=TabBtn.app_log):
            switcher.current = LogsEnum.app_log.name
            switcher.border_title = self.app.chezmoi.app_log.border_title
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.output_log):
            switcher.current = LogsEnum.output_log.name
            switcher.border_title = self.app.chezmoi.output_log.border_title
        elif (
            self.app.chezmoi.init_cfg.dev_mode
            and event.button.id == self.tab_ids.button_id(btn=TabBtn.debug_log)
        ):
            switcher.current = LogsEnum.debug_log.name
            switcher.border_title = self.app.chezmoi.debug_log.border_title
