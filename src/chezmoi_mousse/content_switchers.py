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
from chezmoi_mousse.constants import (
    FLOW,
    Area,
    BorderTitle,
    NavBtn,
    OperateBtn,
    TabBtn,
    TcssStr,
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


class TreeContentSwitcher(VerticalGroup, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        # updated by OperateTabsBase in on_switch_changed method
        self.expand_all_state: bool = False
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.left),
            classes=TcssStr.tab_left_vertical,
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
            TcssStr.content_switcher_left, TcssStr.border_title_top
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Tree/List Content Switcher
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            if self.expand_all_state:
                self.query_exactly_one(ContentSwitcher).current = (
                    self.tab_ids.tree_id(tree=TreeName.expanded_tree)
                )
            else:
                self.query_exactly_one(ContentSwitcher).current = (
                    self.tab_ids.tree_id(tree=TreeName.managed_tree)
                )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.tree_id(tree=TreeName.flat_tree)
            )


class ViewContentSwitcher(Vertical, AppType):
    def __init__(self, *, tab_ids: TabIds, diff_reverse: bool):
        self.tab_ids = tab_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
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
        ):
            yield DiffView(ids=self.tab_ids, reverse=self.reverse)
            yield ContentsView(ids=self.tab_ids)
            yield GitLogView(ids=self.tab_ids)

    def on_mount(self) -> None:
        self.query_one(ContentSwitcher).add_class(
            TcssStr.content_switcher_right, TcssStr.border_title_top
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.contents):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.view_id(view=ViewName.contents_view)
            )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.diff):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.view_id(view=ViewName.diff_view)
            )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.git_log):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.view_id(view=ViewName.git_log_view)
            )


class InitTabContentSwitcher(Horizontal):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        # updated by OperateTabsBase in on_switch_changed method
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
        )

    def compose(self) -> ComposeResult:
        yield ButtonsVertical(
            tab_ids=self.tab_ids,
            buttons=(NavBtn.new_repo, NavBtn.clone_repo, NavBtn.purge_repo),
            area=Area.left,
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.init_new_view),
            classes=TcssStr.content_switcher_right,
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


class ConfigTabContentSwitcher(Horizontal, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        # updated by OperateTabsBase in on_switch_changed method
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
        )

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_ids.tab_vertical_id(area=Area.left),
            classes=TcssStr.tab_left_vertical,
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
            classes=TcssStr.tab_right_vertical,
        ):
            # TODO: make sure scrollbars appear when there's overflow
            with ContentSwitcher(
                id=self.tab_ids.content_switcher_id(area=Area.right),
                initial=self.tab_ids.view_id(view=ViewName.cat_config),
            ):
                yield Vertical(
                    Label('"chezmoi cat-config" output'),
                    Pretty(self.app.chezmoi.run.cat_config()),
                    id=self.tab_ids.view_id(view=ViewName.cat_config),
                )
                yield Vertical(
                    Label('"chezmoi ignored" output'),
                    Pretty(self.app.chezmoi.run.ignored()),
                    id=self.tab_ids.view_id(view=ViewName.config_ignored),
                )
                yield Vertical(
                    Label('"chezmoi data" output'),
                    Pretty(self.app.chezmoi.run.template_data()),
                    id=self.tab_ids.view_id(view=ViewName.template_data),
                )
                yield Vertical(
                    Label("chezmoi diagram"),
                    Static(FLOW, classes=TcssStr.flow_diagram),
                    id=self.tab_ids.view_id(view=ViewName.diagram),
                )


class LogsTabContentSwitcher(Vertical, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        super().__init__()

    def compose(self) -> ComposeResult:
        tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        if self.app.chezmoi.app_cfg.dev_mode:
            tab_buttons += (TabBtn.debug_log,)

        yield TabBtnHorizontal(
            tab_ids=self.tab_ids, buttons=tab_buttons, area=Area.top
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.top),
            initial=self.tab_ids.view_id(view=ViewName.app_log_view),
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        content_switcher = self.query_exactly_one(ContentSwitcher)

        if event.button.id == self.tab_ids.button_id(btn=TabBtn.app_log):
            content_switcher.current = self.tab_ids.view_id(
                view=ViewName.app_log_view
            )
            content_switcher.border_title = BorderTitle.app_log
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.output_log):
            content_switcher.current = self.tab_ids.view_id(
                view=ViewName.output_log_view
            )
            content_switcher.border_title = BorderTitle.output_log
        elif (
            self.app.chezmoi.app_cfg.dev_mode
            and event.button.id == self.tab_ids.button_id(btn=TabBtn.debug_log)
        ):
            content_switcher.current = self.tab_ids.view_id(
                view=ViewName.debug_log_view
            )
            content_switcher.border_title = BorderTitle.debug_log
