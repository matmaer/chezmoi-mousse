import json

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import ContentSwitcher, Label, Pretty, Static

from chezmoi_mousse import AreaName, CanvasIds, Tcss, TreeName, ViewName
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.rich_logs import (
    AppLog,
    ContentsView,
    DebugLog,
    DiffView,
    OutputLog,
)
from chezmoi_mousse.gui.tree_widgets import ExpandedTree, FlatTree, ManagedTree
from chezmoi_mousse.gui.widgets import DoctorListView, DoctorTable, GitLogView

__all__ = [
    "ConfigTabSwitcher",
    "HelpTabSwitcher",
    "LogsTabSwitcher",
    "TreeSwitcher",
    "ViewSwitcher",
]


class TreeSwitcher(ContentSwitcher, AppType):

    def __init__(self, canvas_ids: CanvasIds):
        self.canvas_ids = canvas_ids
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.left),
            initial=self.canvas_ids.tree_id(tree=TreeName.managed_tree),
            classes=Tcss.content_switcher_left.name,
        )

    def compose(self) -> ComposeResult:
        yield ManagedTree(canvas_ids=self.canvas_ids)
        yield FlatTree(canvas_ids=self.canvas_ids)
        yield ExpandedTree(canvas_ids=self.canvas_ids)

    def on_mount(self) -> None:
        self.border_title = " destDir "
        self.add_class(Tcss.border_title_top.name)


class ViewSwitcher(ContentSwitcher, AppType):
    def __init__(self, *, canvas_ids: CanvasIds, diff_reverse: bool):
        self.canvas_ids = canvas_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.right),
            initial=self.canvas_ids.view_id(view=ViewName.diff_view),
        )

    def compose(self) -> ComposeResult:
        yield DiffView(canvas_ids=self.canvas_ids, reverse=self.reverse)
        yield ContentsView(canvas_ids=self.canvas_ids)
        yield GitLogView(canvas_ids=self.canvas_ids)


class ConfigTabSwitcher(ContentSwitcher, AppType):

    doctor_stdout: reactive[str | None] = reactive(None)
    cat_config_stdout: reactive[str | None] = reactive(None)
    ignored_stdout: reactive[str | None] = reactive(None)
    template_data_stdout: reactive[str | None] = reactive(None)

    def __init__(self, canvas_ids: CanvasIds):
        self.canvas_ids = canvas_ids
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.right),
            initial=self.canvas_ids.view_id(view=ViewName.doctor_view),
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
            id=self.canvas_ids.view_id(view=ViewName.doctor_view),
            classes=Tcss.doctor_vertical_scroll.name,
        )
        yield Vertical(
            Label(
                '"chezmoi cat-config" output', classes=Tcss.section_label.name
            ),
            Pretty("<cat-config>", id=ViewName.pretty_cat_config_view),
            id=self.canvas_ids.view_id(view=ViewName.cat_config_view),
        )
        yield Vertical(
            Label('"chezmoi ignored" output', classes=Tcss.section_label.name),
            Pretty("<ignored>", id=ViewName.pretty_ignored_view),
            id=self.canvas_ids.view_id(view=ViewName.git_ignored_view),
        )
        yield Vertical(
            Label('"chezmoi data" output', classes=Tcss.section_label.name),
            Pretty("<template_data>", id=ViewName.pretty_template_data_view),
            id=self.canvas_ids.view_id(view=ViewName.template_data_view),
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

    def __init__(self, canvas_ids: CanvasIds):
        self.canvas_ids = canvas_ids
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.right),
            initial=self.canvas_ids.view_id(view=ViewName.diagram_view),
            classes=Tcss.nav_content_switcher.name,
        )

    def compose(self) -> ComposeResult:

        yield Vertical(
            Label("chezmoi diagram", classes=Tcss.section_label.name),
            Static(self.FLOW_DIAGRAM, classes=Tcss.flow_diagram.name),
            id=self.canvas_ids.view_id(view=ViewName.diagram_view),
        )


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, canvas_ids: CanvasIds, dev_mode: bool):
        self.canvas_ids = canvas_ids
        self.dev_mode = dev_mode
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.top),
            initial=self.canvas_ids.view_id(view=ViewName.app_log_view),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield AppLog(canvas_ids=self.canvas_ids)
        yield OutputLog(canvas_ids=self.canvas_ids)
        if self.dev_mode is True:
            yield DebugLog(canvas_ids=self.canvas_ids)

    def on_mount(self) -> None:
        self.border_title = " App Log "
