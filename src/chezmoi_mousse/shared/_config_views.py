import json
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Pretty, Static

from chezmoi_mousse import CommandResult, ViewName

from ._section_headers import SectionLabel, SectionLabelText

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["CatConfigView", "IgnoredView", "TemplateDataView"]


class CatConfigView(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.views.cat_config)

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.cat_config_output)

    def mount_cat_config_output(self, command_result: CommandResult) -> None:
        self.mount(ScrollableContainer(Static(command_result.std_out)))


class IgnoredView(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.views.ignored)

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.ignored_output)

    def mount_ignored_output(self, command_result: CommandResult) -> None:
        self.mount(
            ScrollableContainer(Pretty(command_result.std_out.splitlines()))
        )


class TemplateDataView(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.template_data_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.template_data_output)

    def mount_template_data_output(
        self, command_result: CommandResult
    ) -> None:
        parsed = json.loads(command_result.std_out)
        self.mount(
            ScrollableContainer(
                Pretty(parsed, id=ViewName.pretty_template_data_view)
            )
        )
