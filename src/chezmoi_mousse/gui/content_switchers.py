import json

from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.validation import URL
from textual.widgets import (
    ContentSwitcher,
    Input,
    Label,
    Pretty,
    Select,
    Static,
)

from chezmoi_mousse import Area, OperateBtn, TabIds, Tcss, TreeName, ViewName
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.button_groups import OperateBtnHorizontal
from chezmoi_mousse.gui.rich_logs import (
    AppLog,
    ContentsView,
    DebugLog,
    DiffView,
    OutputLog,
)
from chezmoi_mousse.gui.widgets import (
    DoctorListView,
    DoctorTable,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
)

__all__ = [
    "ConfigTabSwitcher",
    "HelpTabSwitcher",
    "InitTabSwitcher",
    "LogsTabSwitcher",
    "TreeSwitcher",
    "ViewSwitcher",
]


class TreeSwitcher(ContentSwitcher, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.left),
            initial=self.tab_ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        )
        # updated by OperateTabsBase in on_switch_changed method
        self.expand_all_state: bool = False

    def compose(self) -> ComposeResult:
        yield ManagedTree(tab_ids=self.tab_ids)
        yield FlatTree(tab_ids=self.tab_ids)
        yield ExpandedTree(tab_ids=self.tab_ids)

    def on_mount(self) -> None:
        self.border_title = str(self.app.destDir)
        self.add_class(Tcss.border_title_top.name)


class ViewSwitcher(ContentSwitcher, AppType):
    def __init__(self, *, tab_ids: TabIds, diff_reverse: bool):
        self.tab_ids = tab_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.diff_view),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield DiffView(init_ids=self.tab_ids, reverse=self.reverse)
        yield ContentsView(tab_ids=self.tab_ids)
        yield GitLogView(tab_ids=self.tab_ids)

    def on_mount(self) -> None:
        self.border_title = str(self.app.destDir)
        self.add_class(Tcss.border_title_top.name)


class InitTabSwitcher(ContentSwitcher):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.init_new_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:
        # New Repo Content
        yield Vertical(
            Label(
                "Initialize new chezmoi git repository",
                classes=Tcss.section_label.name,
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
                classes=Tcss.section_label.name,
            ),
            # TODO: implement guess feature from chezmoi
            # TODO: add selection for https(with PAT token) or ssh
            HorizontalGroup(
                Vertical(
                    Select[str].from_values(
                        ["https", "ssh"],
                        classes=Tcss.input_select.name,
                        value="https",
                        allow_blank=False,
                        type_to_search=False,
                    ),
                    classes=Tcss.input_select_vertical.name,
                ),
                Vertical(
                    Input(
                        placeholder="Enter repository URL",
                        validate_on=["submitted"],
                        validators=URL(),
                        classes=Tcss.input_field.name,
                    ),
                    classes=Tcss.input_field_vertical.name,
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
                classes=Tcss.section_label.name,
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

    doctor_stdout: reactive[str | None] = reactive(None)
    cat_config_stdout: reactive[str | None] = reactive(None)
    ignored_stdout: reactive[str | None] = reactive(None)
    template_data_stdout: reactive[str | None] = reactive(None)

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.doctor_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Label('"chezmoi doctor" output', classes=Tcss.section_label.name),
            DoctorTable(),
            Label(
                "Password managers not found in $PATH",
                classes=Tcss.section_label.name,
            ),
            DoctorListView(),
            id=self.tab_ids.view_id(view=ViewName.doctor_view),
            classes=Tcss.doctor_vertical_scroll.name,
        )
        yield Vertical(
            Label(
                '"chezmoi cat-config" output', classes=Tcss.section_label.name
            ),
            Pretty("<cat-config>", id=ViewName.pretty_cat_config_view),
            id=self.tab_ids.view_id(view=ViewName.cat_config_view),
        )
        yield Vertical(
            Label('"chezmoi ignored" output', classes=Tcss.section_label.name),
            Pretty("<ignored>", id=ViewName.pretty_ignored_view),
            id=self.tab_ids.view_id(view=ViewName.git_ignored_view),
        )
        yield Vertical(
            Label('"chezmoi data" output', classes=Tcss.section_label.name),
            Pretty("<template_data>", id=ViewName.pretty_template_data_view),
            id=self.tab_ids.view_id(view=ViewName.template_data_view),
        )

    def watch_doctor_stdout(self):
        doctor_table = self.query_exactly_one(DoctorTable)
        if self.doctor_stdout is None:
            return
        pw_mgr_cmds: list[str] = doctor_table.populate_doctor_data(
            doctor_data=self.doctor_stdout.splitlines()
        )
        doctor_list_view = self.query_exactly_one(DoctorListView)
        doctor_list_view.populate_listview(pw_mgr_cmds)

    def watch_cat_config_stdout(self):
        if self.cat_config_stdout is None:
            return
        pretty_cat_config = self.query_one(
            f"#{ViewName.pretty_cat_config_view}", Pretty
        )
        pretty_cat_config.update(self.cat_config_stdout.splitlines())

    def watch_ignored_stdout(self):
        if self.ignored_stdout is None:
            return
        pretty_ignored = self.query_one(
            f"#{ViewName.pretty_ignored_view}", Pretty
        )
        pretty_ignored.update(self.ignored_stdout.splitlines())

    def watch_template_data_stdout(self):
        if self.template_data_stdout is None:
            return
        pretty_template_data = self.query_one(
            f"#{ViewName.pretty_template_data_view}", Pretty
        )
        template_data_json = json.loads(self.template_data_stdout)
        pretty_template_data.update(template_data_json)


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
            initial=self.tab_ids.view_id(view=ViewName.diagram_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:

        yield Vertical(
            Label("chezmoi diagram", classes=Tcss.section_label.name),
            Static(self.FLOW_DIAGRAM, classes=Tcss.flow_diagram.name),
            id=self.tab_ids.view_id(view=ViewName.diagram_view),
        )


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.top),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield AppLog()
        yield OutputLog()
        if self.app.dev_mode:
            yield DebugLog()
