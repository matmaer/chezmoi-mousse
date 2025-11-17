from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
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
    FlatSectionLabel,
    SectionLabel,
    SubSectionLabel,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["HelpTab"]

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


class HelpSections(StrEnum):
    chezmoi_diagram = "Chezmoi Diagram"
    filters_section_label = "Available Filters"
    # Add tab
    add_tab_help = "Add Tab Help"
    add_dir_button = f"{OperateBtn.add_dir.label()} Button"
    add_file_button = f"{OperateBtn.add_file.label()} Button"
    unmanaged_dirs_filter = f"{Switches.unmanaged_dirs.label} Filter"
    unwanted_filter = f"{Switches.unwanted.label} Filter"
    # Apply tab
    apply_tab_help = "Apply Tab Help"
    apply_dir_button = f"{OperateBtn.apply_path.label(PathType.DIR)} Button"
    apply_file_button = f"{OperateBtn.apply_path.label(PathType.FILE)} Button"
    # Re-Add tab
    re_add_tab_help = "Re-Add Tab Help"
    re_add_dir_button = f"{OperateBtn.re_add_path.label(PathType.DIR)} Button"
    re_add_file_button = (
        f"{OperateBtn.re_add_path.label(PathType.FILE)} Button"
    )
    # Common buttons for Apply and Re-Add tabs
    destroy_dir_button = (
        f"{OperateBtn.destroy_path.label(PathType.DIR)} Button"
    )
    destroy_file_button = (
        f"{OperateBtn.destroy_path.label(PathType.FILE)} Button"
    )
    forget_dir_button = f"{OperateBtn.forget_path.label(PathType.DIR)} Button"
    forget_file_button = (
        f"{OperateBtn.forget_path.label(PathType.FILE)} Button"
    )
    # Common filters for Apply and Re-Add tabs
    expand_all_filter = f"{Switches.expand_all.label} Filter"
    unchanged_filter = f"{Switches.unchanged.label} Filter"


class SharedBtnHelp(VerticalGroup):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__()
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_forget)
        yield SubSectionLabel(HelpSections.forget_file_button)
        yield Static(OperateBtn.forget_path.file_tooltip)
        yield SubSectionLabel(HelpSections.forget_dir_button)
        yield Static(OperateBtn.forget_path.dir_tooltip)

        yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_destroy)
        yield SubSectionLabel(HelpSections.destroy_file_button)
        yield Static(OperateBtn.destroy_path.file_tooltip)
        yield SubSectionLabel(HelpSections.destroy_dir_button)
        yield Static(OperateBtn.destroy_path.dir_tooltip)


class SharedFiltersHelp(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(HelpSections.filters_section_label)
        yield SubSectionLabel(HelpSections.unchanged_filter)
        yield Static(Switches.unchanged.enabled_tooltip)
        yield SubSectionLabel(HelpSections.expand_all_filter)
        yield Static(Switches.expand_all.enabled_tooltip)


class ApplyTabHelp(Vertical):
    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        self.view_id = self.ids.view_id(view=ViewName.apply_help_view)
        super().__init__(id=self.view_id)

    def compose(self) -> ComposeResult:
        yield SectionLabel(HelpSections.apply_tab_help)
        with VerticalScroll():
            yield SharedFiltersHelp()
            yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_apply)
            yield SubSectionLabel(HelpSections.apply_file_button)
            yield Static(OperateBtn.apply_path.file_tooltip)
            yield SubSectionLabel(HelpSections.apply_dir_button)
            yield Static(OperateBtn.apply_path.dir_tooltip)
            yield SharedBtnHelp(ids=self.ids)


class ReAddTabHelp(VerticalScroll):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        self.view_id = self.ids.view_id(view=ViewName.re_add_help_view)
        super().__init__(id=self.view_id)

    def compose(self) -> ComposeResult:
        yield SectionLabel(HelpSections.re_add_tab_help)
        with VerticalScroll():
            yield SharedFiltersHelp()
            yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_re_add)
            yield SubSectionLabel(HelpSections.re_add_file_button)
            yield Static(OperateBtn.re_add_path.file_tooltip)
            yield SubSectionLabel(HelpSections.re_add_dir_button)
            yield Static(OperateBtn.re_add_path.dir_tooltip)
            yield SharedBtnHelp(ids=self.ids)


class AddTabHelp(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.views.add_help)

    def compose(self) -> ComposeResult:
        yield SectionLabel(HelpSections.add_tab_help)

        with VerticalScroll():
            yield FlatSectionLabel(HelpSections.filters_section_label)
            yield SubSectionLabel(HelpSections.unmanaged_dirs_filter)
            yield Static(Switches.unmanaged_dirs.enabled_tooltip)
            yield SubSectionLabel(HelpSections.unwanted_filter)
            yield Static(Switches.unwanted.enabled_tooltip)
            yield FlatLink(ids=self.ids, link_enum=LinkBtn.chezmoi_add)
            yield SubSectionLabel(HelpSections.add_file_button)
            yield Static(OperateBtn.apply_path.file_tooltip)
            yield SubSectionLabel(HelpSections.add_dir_button)
            yield Static(OperateBtn.apply_path.dir_tooltip)


class ChezmoiDiagram(Vertical):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.diagram_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(HelpSections.chezmoi_diagram)
        yield ScrollableContainer(
            Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram.name)
        )


class HelpTabSwitcher(ContentSwitcher):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        self.content_switcher_id = self.ids.content_switcher_id(
            name=ContainerName.help_switcher
        )
        super().__init__(
            id=self.content_switcher_id,
            initial=self.ids.view_id(view=ViewName.apply_help_view),
        )

    def compose(self) -> ComposeResult:

        yield ApplyTabHelp(ids=self.ids)
        yield ReAddTabHelp(ids=self.ids)
        yield AddTabHelp(ids=self.ids)
        yield ChezmoiDiagram(ids=self.ids)


class HelpTab(Horizontal):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(id=ids.canvas_container_id)

        self.content_switcher_qid = self.ids.content_switcher_id(
            "#", name=ContainerName.help_switcher
        )

    def compose(self) -> ComposeResult:
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
        if event.button.id == self.ids.views.apply_help_btn:
            switcher.current = self.ids.views.apply_help
        elif event.button.id == self.ids.views.re_add_help_btn:
            switcher.current = self.ids.views.re_add_help
        elif event.button.id == self.ids.views.add_help_btn:
            switcher.current = self.ids.views.add_help
        elif event.button.id == self.ids.views.diagram_btn:
            switcher.current = self.ids.views.diagram
