from __future__ import annotations

import json
from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.reactive import reactive
from textual.widgets import (
    ContentSwitcher,
    Pretty,
    Static,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.ascii_constants import FLOW_DIAGRAM
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.doctor_data import DoctorTable
from chezmoi_mousse.gui.common.messages import FlatBtnMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    Tcss,
)

from .common.actionables import (
    FlatBtn,
    FlatButtonsVertical,
)

if TYPE_CHECKING:
    from textual.app import ComposeResult


__all__ = ["ConfigTab"]


class ConfigTab(TabPane):
    class CatConfigStatic(Static): ...

    class PrettyIgnored(Pretty): ...

    class PrettyTemplateData(Pretty): ...

    template_data: reactive[str | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(id=BtnLabel.config.pane_id, title=BtnLabel.config)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                app_ids=store.config_ids,
                labels=(
                    BtnLabel.doctor,
                    BtnLabel.cat_config,
                    BtnLabel.ignored,
                    BtnLabel.template_data,
                    BtnLabel.diagram,
                ),
            )
            with ContentSwitcher(initial=store.config_ids.container.doctor):
                yield Vertical(
                    MainSectionLabel(LabelStr.doctor_output),
                    DoctorTable(),
                    id=store.config_ids.container.doctor,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.cat_config_output),
                    ConfigTab.CatConfigStatic("Not Found"),
                    id=store.config_ids.container.cat_config,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.ignored_output),
                    ScrollableContainer(ConfigTab.PrettyIgnored("Not Found")),
                    id=store.config_ids.container.ignored,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.template_data_output),
                    ScrollableContainer(ConfigTab.PrettyTemplateData("Not Found")),
                    id=store.config_ids.container.template_data,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.diagram),
                    Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram),
                    id=store.config_ids.container.diagram,
                )

    @on(FlatBtnMsg)
    def switch_content(self, msg: FlatBtnMsg) -> None:
        if not isinstance(msg.button, FlatBtn):
            return
        msg.stop()

        if msg.button.label == BtnLabel.doctor.value:
            self.switcher.current = store.config_ids.container.doctor
        elif msg.button.label == BtnLabel.cat_config:
            self.switcher.current = store.config_ids.container.cat_config
        elif msg.button.label == BtnLabel.ignored:
            self.switcher.current = store.config_ids.container.ignored
        elif msg.button.label == BtnLabel.template_data:
            self.switcher.current = store.config_ids.container.template_data
        elif msg.button.label == BtnLabel.diagram:
            self.switcher.current = store.config_ids.container.diagram

    def _parse_template_data(self, template_data: str) -> None:
        parsed_data = json.loads(template_data)
        widget = self.query_exactly_one(ConfigTab.PrettyTemplateData)
        widget.update(parsed_data)

    def watch_template_data(self, template_data: str | None) -> None:
        if template_data is not None:
            self._parse_template_data(template_data)
