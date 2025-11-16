from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, ContentSwitcher, Static

from chezmoi_mousse import (
    ContainerName,
    FlatBtn,
    LinkBtn,
    OperateBtn,
    PathType,
    Switches,
    Tcss,
    ViewName,
)
from chezmoi_mousse.shared import (
    FlatButtonsVertical,
    FlatLink,
    SectionLabel,
    SubSectionLabel,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["HelpTab"]


class HelpTabSections(StrEnum):
    available_buttons = "Available Buttons"
    available_switches = "Available Filters"
    chezmoi_diagram = "chezmoi diagram"


class ToolTipText(Static):

    def on_mount(self) -> None:
        self.styles.margin = (1, 2, 1, 2)


class SharedBtnHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__()
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield SubSectionLabel(OperateBtn.forget_path.label(PathType.FILE))
        yield ToolTipText(OperateBtn.forget_path.file_tooltip)

        yield SubSectionLabel(OperateBtn.forget_path.label(PathType.DIR))
        yield ToolTipText(OperateBtn.forget_path.dir_tooltip)

        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_forget)

        yield SubSectionLabel(OperateBtn.destroy_path.label(PathType.FILE))
        yield ToolTipText(OperateBtn.destroy_path.file_tooltip)

        yield SubSectionLabel(OperateBtn.destroy_path.label(PathType.DIR))
        yield ToolTipText(OperateBtn.destroy_path.dir_tooltip)

        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_destroy)

    def on_mount(self) -> None:
        self.styles.height = "auto"


class SharedFiltersHelp(Vertical):

    def compose(self) -> ComposeResult:
        yield SectionLabel(HelpTabSections.available_switches)

        yield SubSectionLabel(Switches.unchanged.label)
        yield ToolTipText(Switches.unchanged.enabled_tooltip)

        yield SubSectionLabel(Switches.expand_all.label)
        yield ToolTipText(Switches.expand_all.enabled_tooltip)

    def on_mount(self) -> None:
        self.styles.height = "auto"


class ApplyTabHelp(ScrollableContainer):

    def __init__(self, ids: "CanvasIds") -> None:
        self.view_id = ids.view_id(view=ViewName.apply_help_view)
        super().__init__(id=self.view_id)

        self.ids = ids
        self.shared_filters_help_id = f"{self.view_id}_filters_help"

    def compose(self) -> ComposeResult:
        yield SharedFiltersHelp(id=self.shared_filters_help_id)

        yield SectionLabel(HelpTabSections.available_buttons)

        yield SubSectionLabel(OperateBtn.apply_path.label(PathType.FILE))
        yield ToolTipText(OperateBtn.apply_path.file_tooltip)

        yield SubSectionLabel(OperateBtn.apply_path.label(PathType.DIR))
        yield ToolTipText(OperateBtn.apply_path.dir_tooltip)

        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_apply)
        yield SharedBtnHelp(ids=self.ids)


class ReAddTabHelp(ScrollableContainer):

    def __init__(self, ids: "CanvasIds") -> None:
        self.view_id = ids.view_id(view=ViewName.re_add_help_view)
        super().__init__(id=self.view_id)

        self.ids = ids
        self.shared_filters_help_id = f"{self.view_id}_filters_help"

    def compose(self) -> ComposeResult:
        yield SharedFiltersHelp(id=self.shared_filters_help_id)

        yield SectionLabel(HelpTabSections.available_buttons)

        yield SubSectionLabel(OperateBtn.re_add_path.label(PathType.FILE))
        yield ToolTipText(OperateBtn.re_add_path.file_tooltip)

        yield SubSectionLabel(OperateBtn.re_add_path.label(PathType.DIR))
        yield ToolTipText(OperateBtn.re_add_path.dir_tooltip)

        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_re_add)
        yield SharedBtnHelp(ids=self.ids)


class AddTabHelp(ScrollableContainer):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__(id=ids.view_id(view=ViewName.add_help_view))
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield SectionLabel(HelpTabSections.available_switches)

        yield SubSectionLabel(Switches.unmanaged_dirs.label)
        yield ToolTipText(Switches.unmanaged_dirs.enabled_tooltip)

        yield SubSectionLabel(Switches.unwanted.label)
        yield ToolTipText(Switches.unwanted.enabled_tooltip)

        yield SectionLabel(HelpTabSections.available_buttons)

        yield SubSectionLabel(OperateBtn.add_file.label())
        yield ToolTipText(OperateBtn.add_file.enabled_tooltip)

        yield SubSectionLabel(OperateBtn.add_dir.label())
        yield ToolTipText(OperateBtn.add_dir.enabled_tooltip)

        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_add)


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
┌──────┴───────┐    ┌──────┴───────────────────┴───────┐    ┌──────┴───────┐
│ destination  │    │    target state / source state   │    │  git remote  │
└──────────────┘    └──────────────────────────────────┘    └──────────────┘
"""

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.content_switcher_id(name=ContainerName.help_switcher),
            initial=self.ids.view_id(view=ViewName.apply_help_view),
        )

    def compose(self) -> ComposeResult:

        yield ApplyTabHelp(ids=self.ids)
        yield ReAddTabHelp(ids=self.ids)
        yield AddTabHelp(ids=self.ids)
        yield ScrollableContainer(
            SectionLabel(HelpTabSections.chezmoi_diagram),
            Static(self.FLOW_DIAGRAM, classes=Tcss.flow_diagram.name),
            id=self.ids.view_id(view=ViewName.diagram_view),
        )


class HelpTab(Horizontal):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=ids.canvas_container_id)

        # Content Switcher IDs
        self.content_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.help_switcher
        )
        self.content_switcher_qid = self.ids.content_switcher_id(
            "#", name=ContainerName.help_switcher
        )
        # View IDs
        self.apply_help_view_id = self.ids.view_id(
            view=ViewName.apply_help_view
        )
        self.re_add_help_view_id = self.ids.view_id(
            view=ViewName.re_add_help_view
        )
        self.add_help_view_id = self.ids.view_id(view=ViewName.add_help_view)
        self.diagram_view_id = self.ids.view_id(view=ViewName.diagram_view)
        # Button IDs
        self.apply_help_btn_id = self.ids.button_id(btn=FlatBtn.apply_help)
        self.re_add_help_btn_id = self.ids.button_id(btn=FlatBtn.re_add_help)
        self.add_help_btn_id = self.ids.button_id(btn=FlatBtn.add_help)
        self.diagram_btn_id = self.ids.button_id(btn=FlatBtn.diagram)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=self.ids.tab_vertical_id(name=ContainerName.left_side),
            classes=Tcss.tab_left_vertical.name,
        ):
            yield FlatButtonsVertical(
                ids=self.ids,
                buttons=(
                    FlatBtn.apply_help,
                    FlatBtn.re_add_help,
                    FlatBtn.add_help,
                    FlatBtn.diagram,
                ),
            )
        yield HelpTabSwitcher(ids=self.ids)

    @on(Button.Pressed, Tcss.flat_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(self.content_switcher_qid, HelpTabSwitcher)
        if event.button.id == self.apply_help_btn_id:
            switcher.current = self.apply_help_view_id
        elif event.button.id == self.re_add_help_btn_id:
            switcher.current = self.re_add_help_view_id
        elif event.button.id == self.add_help_btn_id:
            switcher.current = self.add_help_view_id
        elif event.button.id == self.diagram_btn_id:
            switcher.current = self.diagram_view_id
