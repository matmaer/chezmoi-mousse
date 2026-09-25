from __future__ import annotations

import json
from typing import TYPE_CHECKING

from textual import on, work
from textual.containers import (
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.reactive import reactive
from textual.widgets import (
    Button,
    ContentSwitcher,
    Pretty,
    Static,
    TabPane,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.ascii_constants import FLOW_DIAGRAM
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.doctor_data import DoctorTable
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    ReadCmd,
    Tcss,
)

from .common.actionables import FlatButtonsVertical

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from chezmoi_mousse.named_tuples import CommandResult


__all__ = ["ConfigTab"]


class ConfigTab(TabPane):
    class CatConfigStatic(Static): ...

    class PrettyGitConfig(Pretty): ...

    class PrettyIgnored(Pretty): ...

    class PrettyTemplateData(Pretty): ...

    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(id=BtnLabel.config.pane_id, title=BtnLabel.config)

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        git_config = self.switcher.query_exactly_one(ConfigTab.PrettyGitConfig)
        git_config.update(store.cfg.git_config_dict)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatButtonsVertical(
                app_ids=store.config_ids,
                labels=(
                    BtnLabel.doctor,
                    BtnLabel.cat_config,
                    BtnLabel.ignored,
                    BtnLabel.template_data,
                    BtnLabel.git_config,
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
                    MainSectionLabel(LabelStr.chezmoi_git_config),
                    ScrollableContainer(ConfigTab.PrettyGitConfig("Not set")),
                    id=store.config_ids.container.git_config,
                )
                yield Vertical(
                    MainSectionLabel(LabelStr.diagram),
                    Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram),
                    id=store.config_ids.container.diagram,
                )

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        if event.button.label == BtnLabel.doctor:
            self.switcher.current = store.config_ids.container.doctor
        elif event.button.label == BtnLabel.cat_config:
            self.switcher.current = store.config_ids.container.cat_config
        elif event.button.label == BtnLabel.ignored:
            self.switcher.current = store.config_ids.container.ignored
        elif event.button.label == BtnLabel.template_data:
            self.switcher.current = store.config_ids.container.template_data
        elif event.button.label == BtnLabel.git_config:
            self.switcher.current = store.config_ids.container.git_config
        elif event.button.label == BtnLabel.diagram:
            self.switcher.current = store.config_ids.container.diagram

    @work
    async def _update_widget(self, cmd_result: CommandResult) -> None:
        if cmd_result.cmd_enum == ReadCmd.doctor:
            widget = self.query_exactly_one(DoctorTable)
            widget.populate_dr_table(cmd_result.std_out)
        elif cmd_result.cmd_enum == ReadCmd.cat_config:
            widget = self.query_exactly_one(ConfigTab.CatConfigStatic)
            widget.update(cmd_result.std_out)
        elif cmd_result.cmd_enum == ReadCmd.ignored:
            widget = self.query_exactly_one(ConfigTab.PrettyIgnored)
            widget.update(cmd_result.std_out)
        elif cmd_result.cmd_enum == ReadCmd.template_data:
            parsed_data = json.loads(cmd_result.std_out)
            widget = self.query_exactly_one(ConfigTab.PrettyTemplateData)
            widget.update(parsed_data)

    def watch_cmd_result(self, cmd_result: CommandResult | None) -> None:
        if cmd_result is None:
            return
        self._update_widget(cmd_result)
