from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.highlight import highlight
from textual.reactive import reactive
from textual.widgets import Button, ContentSwitcher, Pretty, Static, TabPane

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.ascii_constants import FLOW_DIAGRAM
from chezmoi_mousse.gui.common.doctor_data import DoctorTable
from chezmoi_mousse.str_enums import BtnLabel, LabelStr, ReadCmd, Tcss

from .common.actionables import FlatBtnGroup

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import CommandResult


__all__ = ["ConfigTab"]


class CatConfigStatic(Static): ...


class DumpConfigStatic(Static): ...


class PrettyIgnored(Pretty): ...


class TemplateDataStatic(Static): ...


class ConfigTab(TabPane):
    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FlatBtnGroup(
                labels=(
                    BtnLabel.doctor,
                    BtnLabel.cat_config,
                    BtnLabel.dump_config,
                    BtnLabel.ignored,
                    BtnLabel.template_data,
                    BtnLabel.diagram,
                )
            )
            with ContentSwitcher(initial=store.config_ids.container.doctor):
                yield Vertical(
                    Static(LabelStr.doctor_output, classes=Tcss.main_label),
                    DoctorTable(show_cursor=False),
                    id=store.config_ids.container.doctor,
                )
                yield Vertical(
                    Static(LabelStr.cat_config_output, classes=Tcss.main_label),
                    CatConfigStatic(LabelStr.not_set),
                    id=store.config_ids.container.cat_config,
                )
                yield Vertical(
                    Static(LabelStr.dump_config_output, classes=Tcss.main_label),
                    ScrollableContainer(DumpConfigStatic(LabelStr.not_set)),
                    id=store.config_ids.container.dump_config,
                )
                yield Vertical(
                    Static(LabelStr.ignored_output, classes=Tcss.main_label),
                    ScrollableContainer(PrettyIgnored(LabelStr.not_set)),
                    id=store.config_ids.container.ignored,
                )
                yield Vertical(
                    Static(LabelStr.template_data_output, classes=Tcss.main_label),
                    ScrollableContainer(
                        TemplateDataStatic(LabelStr.not_set, markup=False)
                    ),
                    id=store.config_ids.container.template_data,
                )
                yield Vertical(
                    Static(LabelStr.diagram, classes=Tcss.main_label),
                    Static(FLOW_DIAGRAM, classes=Tcss.flow_diagram),
                    id=store.config_ids.container.diagram,
                )

    def on_mount(self) -> None:
        self.switcher = self.query_exactly_one(ContentSwitcher)
        dump_config = self.switcher.query_exactly_one(DumpConfigStatic)
        dump_config.update(highlight(store.cfg.dump_config_std_out, language="json"))

    @on(Button.Pressed)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == BtnLabel.doctor:
            self.switcher.current = store.config_ids.container.doctor
        elif event.button.label == BtnLabel.cat_config:
            self.switcher.current = store.config_ids.container.cat_config
        elif event.button.label == BtnLabel.dump_config:
            self.switcher.current = store.config_ids.container.dump_config
        elif event.button.label == BtnLabel.ignored:
            self.switcher.current = store.config_ids.container.ignored
        elif event.button.label == BtnLabel.template_data:
            self.switcher.current = store.config_ids.container.template_data
        elif event.button.label == BtnLabel.diagram:
            self.switcher.current = store.config_ids.container.diagram

    @work(description="update config tab sections")
    async def _update_widget(self, cmd_result: CommandResult) -> None:
        if cmd_result.cmd_enum == ReadCmd.doctor:
            widget = self.query_exactly_one(DoctorTable)
            widget.populate_dr_table(cmd_result.std_out)
        elif cmd_result.cmd_enum == ReadCmd.cat_config:
            widget = self.query_exactly_one(CatConfigStatic)
            widget.update(cmd_result.std_out)
        elif cmd_result.cmd_enum == ReadCmd.ignored:
            widget = self.query_exactly_one(PrettyIgnored)
            widget.update(cmd_result.std_out)
        elif cmd_result.cmd_enum == ReadCmd.template_data:
            widget = self.query_exactly_one(TemplateDataStatic)
            widget.update(highlight(cmd_result.std_out, language="json"))
        else:
            self.notify(f"Unhandled cmd result for {cmd_result.cmd_enum}")

    def watch_cmd_result(self, cmd_result: CommandResult | None) -> None:
        if cmd_result is None:
            return
        self._update_widget(cmd_result)
