import json

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalScroll
from textual.validation import URL
from textual.widgets import (
    ContentSwitcher,
    Input,
    Label,
    Pretty,
    Select,
    Static,
)

from chezmoi_mousse.button_groups import OperateBtnHorizontal
from chezmoi_mousse.chezmoi import ReadCmd
from chezmoi_mousse.id_typing import AppType, TabIds
from chezmoi_mousse.id_typing.enums import (
    Area,
    OperateBtn,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.logs_tab import AppLog, DebugLog, OutputLog
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    DoctorListView,
    DoctorTable,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
)


class TreeSwitcher(ContentSwitcher, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.left),
            initial=self.tab_ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left,
        )
        # updated by OperateTabsBase in on_switch_changed method
        self.expand_all_state: bool = False

    def compose(self) -> ComposeResult:
        yield ManagedTree(tab_ids=self.tab_ids)
        yield FlatTree(tab_ids=self.tab_ids)
        yield ExpandedTree(tab_ids=self.tab_ids)

    def on_mount(self) -> None:
        self.border_title = str(self.app.destDir)
        self.add_class(Tcss.border_title_top)


class ViewSwitcher(ContentSwitcher, AppType):
    def __init__(self, *, tab_ids: TabIds, diff_reverse: bool):
        self.tab_ids = tab_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.diff_view),
            classes=Tcss.border_title_top,
        )

    def compose(self) -> ComposeResult:
        yield DiffView(tab_ids=self.tab_ids, reverse=self.reverse)
        yield ContentsView(tab_ids=self.tab_ids)
        yield GitLogView(tab_ids=self.tab_ids)

    def on_mount(self) -> None:
        self.border_title = str(self.app.destDir)
        self.add_class(Tcss.border_title_top)


class InitTabSwitcher(ContentSwitcher):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.init_new_view),
            classes=Tcss.nav_content_switcher,
        )

    def compose(self) -> ComposeResult:
        # New Repo Content
        yield Vertical(
            Label(
                "Initialize new chezmoi git repository",
                classes=Tcss.section_label,
            ),
            Input(placeholder="Enter config file path"),
            OperateBtnHorizontal(
                tab_ids=self.tab_ids, buttons=(OperateBtn.new_repo,)
            ),
            id=self.tab_ids.view_id(view=ViewName.init_new_view),
        )
        # Clone Repo Content
        yield Vertical(
            Label(
                "Clone existing chezmoi git repository",
                classes=Tcss.section_label,
            ),
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
            Label(
                "Purge current chezmoi git repository",
                classes=Tcss.section_label,
            ),
            Static(
                "Remove chezmoi's configuration, state, and source directory, but leave the target state intact."
            ),
            OperateBtnHorizontal(
                tab_ids=self.tab_ids, buttons=(OperateBtn.purge_repo,)
            ),
            id=self.tab_ids.view_id(view=ViewName.init_purge_view),
        )


class ConfigTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.doctor),
            classes=Tcss.nav_content_switcher,
        )

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label('"chezmoi doctor" output', classes=Tcss.section_label),
            DoctorTable(),
            Label(
                "Password managers not found in $PATH",
                classes=Tcss.section_label,
            ),
            DoctorListView(),
            id=self.tab_ids.view_id(view=ViewName.doctor),
            classes=Tcss.doctor_vertical_scroll,
        )
        yield Vertical(
            Label('"chezmoi cat-config" output', classes=Tcss.section_label),
            Pretty(self.app.chezmoi.read(ReadCmd.cat_config).splitlines()),
            id=self.tab_ids.view_id(view=ViewName.cat_config),
        )
        yield Vertical(
            Label('"chezmoi ignored" output', classes=Tcss.section_label),
            Pretty(self.app.chezmoi.read(ReadCmd.ignored).splitlines()),
            id=self.tab_ids.view_id(view=ViewName.config_ignored),
        )
        yield Vertical(
            Label('"chezmoi data" output', classes=Tcss.section_label),
            Pretty(json.loads(self.app.chezmoi.read(ReadCmd.data))),
            id=self.tab_ids.view_id(view=ViewName.template_data),
        )


class HelpTabSwitcher(ContentSwitcher):

    # provisional diagrams until dynamically created
    FLOW_DIAGRAM = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │                   │                   │                   │
       │     Add Tab       │    autoCommit     │     git push      │
       │   Re-Add Tab      │──────────────────>│──────────────────>│
       │──────────────────>│                   │                   │
       │                   │                autopush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
       │     Apply Tab     │     chezmoi init & chezmoi git pull   │
       │<──────────────────│<──────────────────────────────────────│
       │                   │                   │                   │
       │     Diff View     │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │                   │
       │                   │                   │                   │
       │                   │    chezmoi init & chezmoi git pull    │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │        chezmoi init --one-shot & chezmoi init --apply     │
       │<──────────────────────────────────────────────────────────│
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │ target state │    │ source state │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.flow_diagram),
            classes=Tcss.nav_content_switcher,
        )

    def compose(self) -> ComposeResult:

        yield Vertical(
            Label("chezmoi diagram", classes=Tcss.section_label),
            Static(self.FLOW_DIAGRAM, classes=Tcss.flow_diagram),
            id=self.tab_ids.view_id(view=ViewName.flow_diagram),
        )


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.top),
            classes=Tcss.border_title_top,
        )

    def compose(self) -> ComposeResult:
        yield AppLog()
        yield OutputLog()
        if self.app.chezmoi.dev_mode:
            yield DebugLog()
