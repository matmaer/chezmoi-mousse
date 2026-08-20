from __future__ import annotations

from typing import TYPE_CHECKING

from textual import getters, on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Label, Switch

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.dataclass_types import ReviewBtnData, RunBtnData
from chezmoi_mousse.enum_data import SwitchEnum
from chezmoi_mousse.str_enums import (
    FlatBtnLabel,
    OpBtnLabel,
    OpInfoString,
    TabLabel,
    Tcss,
    WriteCmd,
)

from .messages import ReviewBtnMsg

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_types import ReviewBtnDict
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = [
    "DirContentBtn",
    "ExitOpModalBtn",
    "FlatBtn",
    "RefreshBtn",
    "ReviewBtn",
    "RunBtn",
    "TabBtn",
    "FlatButtonsVertical",
    "ReviewBtnGroup",
    "RunBtnGroup",
    "SwitchSlider",
    "TabButtons",
]


class DirContentBtn(Button):
    def __init__(self, *, label: str, path: Path, app_ids: AppIds) -> None:
        super().__init__(label=label)
        self.path = path
        self.app_ids = app_ids


class ExitOpModalBtn(Button):
    def __init__(self, btn_label: OpBtnLabel, btn_data: RunBtnData) -> None:
        self.bd = btn_data
        super().__init__(
            classes=Tcss.operate_button,
            label=btn_label,
        )


class FlatBtn(Button):
    def __init__(self, ids: AppIds, *, btn_label: FlatBtnLabel) -> None:
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=ids.flat_button_id(btn=btn_label),
            label=btn_label,
            variant="primary",
        )


class RefreshBtn(Button):
    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        super().__init__(
            classes=Tcss.refresh_button,
            id=self.app_ids.op_btn.refresh_tree,
            label=OpBtnLabel.refresh_trees,
        )


class ReviewBtn(Button):
    def __init__(
        self, app_ids: AppIds, btn_label: OpBtnLabel, btn_data: ReviewBtnData
    ) -> None:
        self.app_ids = app_ids
        self.bd = btn_data
        self.btn_label = btn_label
        super().__init__(
            classes=Tcss.operate_button, id=btn_data.btn_id, label=btn_label
        )

    @property
    def review_to_run(self) -> RunBtn:
        mapping = {
            OpBtnLabel.add_review: (
                OpBtnLabel.add_run,
                self.app_ids.op_btn.add_run,
                self.app_ids.op_btn.add_run_q,
            ),
            OpBtnLabel.apply_review: (
                OpBtnLabel.apply_run,
                self.app_ids.op_btn.apply_run,
                self.app_ids.op_btn.apply_run_q,
            ),
            OpBtnLabel.destroy_review: (
                OpBtnLabel.destroy_run,
                self.app_ids.op_btn.destroy_run,
                self.app_ids.op_btn.destroy_run_q,
            ),
            OpBtnLabel.forget_review: (
                OpBtnLabel.forget_run,
                self.app_ids.op_btn.forget_run,
                self.app_ids.op_btn.forget_run_q,
            ),
            OpBtnLabel.re_add_review: (
                OpBtnLabel.re_add_run,
                self.app_ids.op_btn.re_add_run,
                self.app_ids.op_btn.re_add_run_q,
            ),
        }
        run_label, btn_id, btn_qid = mapping[self.btn_label]
        return RunBtn(run_label, RunBtnData(btn_id=btn_id, btn_qid=btn_qid))


class RunBtn(Button):
    def __init__(self, btn_label: OpBtnLabel, btn_data: RunBtnData) -> None:
        self.bd = btn_data
        super().__init__(
            classes=Tcss.operate_button, id=btn_data.btn_id, label=btn_label
        )


class TabBtn(Button):
    def __init__(self, *, app_ids: AppIds, label: TabLabel) -> None:
        super().__init__(classes=Tcss.tab_button, label=label)
        self.app_ids = app_ids


class FlatButtonsVertical(Vertical):
    def __init__(self, ids: AppIds, *, labels: tuple[FlatBtnLabel, ...]) -> None:
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.labels: tuple[FlatBtnLabel, ...] = labels

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield FlatBtn(self.ids, btn_label=label)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatBtn.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatBtn.Pressed) -> None:
        for btn in self.query(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class ToggleDryRunBtn(Button):
    def __init__(self, btn_label: OpBtnLabel, btn_data: RunBtnData) -> None:
        self.bd = btn_data
        super().__init__(
            classes=Tcss.operate_button,
            label=btn_label,
        )


class ReviewBtnGroup(HorizontalGroup):
    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        self.review_buttons: ReviewBtnDict = self._get_review_buttons(app_ids)
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label, btn_data in self.review_buttons.items():
            yield ReviewBtn(self.app_ids, btn_label=btn_label, btn_data=btn_data)

    def set_path_arg(self, path: Path) -> None:
        buttons = self.query_children(ReviewBtn)
        for btn in buttons:
            btn.bd.path_arg = path

    def _get_review_buttons(self, app_ids: AppIds) -> ReviewBtnDict:
        if app_ids.tab_label == TabLabel.add:
            add_review_data = ReviewBtnData(
                ids=app_ids,
                btn_id=app_ids.op_btn.add_review,
                btn_qid=app_ids.op_btn.add_review_q,
                write_cmd=WriteCmd.add,
                op_info_string=OpInfoString.add_path_info,
                op_info_subtitle=OpInfoString.add_subtitle,
            )
            return {
                OpBtnLabel.add_review: add_review_data,
            }
        forget_review_data = ReviewBtnData(
            ids=app_ids,
            btn_id=app_ids.op_btn.forget_review,
            btn_qid=app_ids.op_btn.forget_review_q,
            write_cmd=WriteCmd.forget,
            op_info_string=OpInfoString.forget_path_info,
            op_info_subtitle=OpInfoString.forget_subtitle,
        )
        destroy_review_data = ReviewBtnData(
            ids=app_ids,
            btn_id=app_ids.op_btn.destroy_review,
            btn_qid=app_ids.op_btn.destroy_review_q,
            write_cmd=WriteCmd.destroy,
            op_info_string=OpInfoString.destroy_path_info,
            op_info_subtitle=OpInfoString.destroy_subtitle,
        )
        _forget_destroy_buttons = {
            OpBtnLabel.forget_review: forget_review_data,
            OpBtnLabel.destroy_review: destroy_review_data,
        }
        if app_ids.tab_label == TabLabel.apply:
            apply_review_data = ReviewBtnData(
                ids=app_ids,
                btn_id=app_ids.op_btn.apply_review,
                btn_qid=app_ids.op_btn.apply_review_q,
                write_cmd=WriteCmd.apply,
                op_info_string=OpInfoString.apply_path_info,
                op_info_subtitle=OpInfoString.apply_subtitle,
            )
            return {
                OpBtnLabel.apply_review: apply_review_data,
                **_forget_destroy_buttons,
            }
        elif app_ids.tab_label == TabLabel.re_add:
            op_btn_data = ReviewBtnData(
                ids=app_ids,
                btn_id=app_ids.op_btn.re_add_review,
                btn_qid=app_ids.op_btn.re_add_review_q,
                write_cmd=WriteCmd.re_add,
                op_info_string=OpInfoString.re_add_path_info,
                op_info_subtitle=OpInfoString.re_add_subtitle,
            )
            return {OpBtnLabel.re_add_review: op_btn_data, **_forget_destroy_buttons}
        else:
            raise ValueError(f"Unexpected tab_label {app_ids.tab_label}")

    @on(ReviewBtn.Pressed)
    def handle_review_btn_pressed(self, event: ReviewBtn.Pressed) -> None:
        if isinstance(event.button, ReviewBtn):
            event.stop()
            self.post_message(ReviewBtnMsg(event.button))


class RunBtnGroup(HorizontalGroup):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, btn_pressed: ReviewBtn | RefreshBtn) -> None:
        self.btn = btn_pressed
        super().__init__(
            classes=Tcss.op_btn_group,
        )

    def on_mount(self) -> None:
        if isinstance(self.btn, ReviewBtn):
            toggle_dry_run_btn = self._get_toggle_dry_run_btn(self.btn.app_ids)
            run_button = self._get_run_button(self.btn)
            exit_op_modal_btn = self._get_exit_op_modal_btn(OpBtnLabel.cancel)
            self.mount_all((toggle_dry_run_btn, run_button, exit_op_modal_btn))
        else:
            exit_op_modal_btn = self._get_exit_op_modal_btn(OpBtnLabel.close)
            self.mount(exit_op_modal_btn)

    def update_run_buttons_after_run_command(self, changes: bool) -> None:
        for btn in self.query_children(RunBtn):
            btn.disabled = True
        if changes:
            self.query_exactly_one(ExitOpModalBtn).label = OpBtnLabel.refresh_trees
        else:
            self.query_exactly_one(ExitOpModalBtn).label = OpBtnLabel.close

    def _get_toggle_dry_run_label(self, dry_run: bool) -> OpBtnLabel:
        return OpBtnLabel.add_dry_run if dry_run is True else OpBtnLabel.remove_dry_run

    def _get_exit_op_modal_btn(self, btn_label: OpBtnLabel) -> ExitOpModalBtn:
        return ExitOpModalBtn(
            btn_label,
            RunBtnData(
                btn_id=self.btn.app_ids.op_btn.exit_op_modal,
                btn_qid=self.btn.app_ids.op_btn.exit_op_modal_q,
            ),
        )

    def _get_toggle_dry_run_btn(self, app_ids: AppIds) -> ToggleDryRunBtn:
        return ToggleDryRunBtn(
            self._get_toggle_dry_run_label(self.app.cmattr.dry_run),
            RunBtnData(
                btn_id=app_ids.op_btn.toggle_dry_run,
                btn_qid=app_ids.op_btn.toggle_dry_run_q,
            ),
        )

    def _get_run_button(self, btn: ReviewBtn) -> RunBtn:
        if btn.label == OpBtnLabel.add_review:
            data = RunBtnData(
                btn_id=btn.app_ids.op_btn.add_run,
                btn_qid=btn.app_ids.op_btn.add_run_q,
            )
            return RunBtn(OpBtnLabel.add_run, data)
        elif btn.label == OpBtnLabel.apply_review:
            data = RunBtnData(
                btn_id=btn.app_ids.op_btn.apply_run,
                btn_qid=btn.app_ids.op_btn.apply_run_q,
            )
            return RunBtn(OpBtnLabel.apply_run, data)
        elif btn.label == OpBtnLabel.destroy_review:
            data = RunBtnData(
                btn_id=btn.app_ids.op_btn.destroy_run,
                btn_qid=btn.app_ids.op_btn.destroy_run_q,
            )
            return RunBtn(OpBtnLabel.destroy_run, data)
        elif btn.label == OpBtnLabel.forget_review:
            data = RunBtnData(
                btn_id=btn.app_ids.op_btn.forget_run,
                btn_qid=btn.app_ids.op_btn.forget_run_q,
            )
            return RunBtn(OpBtnLabel.forget_run, data)
        elif btn.label == OpBtnLabel.re_add_review:
            data = RunBtnData(
                btn_id=btn.app_ids.op_btn.re_add_run,
                btn_qid=btn.app_ids.op_btn.re_add_run_q,
            )
            return RunBtn(OpBtnLabel.re_add_run, data)
        else:
            raise ValueError(f"Unexpected button label {btn.label}")

    @on(ToggleDryRunBtn.Pressed)
    def _handle_toggle_dry_run_pressed(self, event: ToggleDryRunBtn.Pressed) -> None:
        event.stop()
        if self.app.cmattr.dry_run and event.button.label != OpBtnLabel.remove_dry_run:
            self.notify("dry run out of sync", severity="error")
        self.app.cmattr.dry_run = not self.app.cmattr.dry_run
        dry_run_btn = self.query_exactly_one(ToggleDryRunBtn)
        dry_run_btn.label = self._get_toggle_dry_run_label(self.app.cmattr.dry_run)


class SwitchWithLabel(HorizontalGroup):
    def __init__(self, ids: AppIds, *, switch_enum: SwitchEnum) -> None:
        super().__init__()
        self.switch_enum = switch_enum
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Switch(id=self.ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class SwitchSlider(VerticalGroup):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.switch_slider, classes="-visible")
        if ids.tab_label in (TabLabel.apply, TabLabel.re_add):
            self.switches = (
                SwitchEnum.show_unchanged,
                SwitchEnum.show_unmanaged,
                SwitchEnum.expand_all,
            )
        else:  # for the AddTab
            self.switches = (SwitchEnum.show_managed, SwitchEnum.show_unwanted)
        self.ids = ids

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            yield SwitchWithLabel(self.ids, switch_enum=switch_enum)

    def on_mount(self) -> None:
        self.query_children(HorizontalGroup).last().styles.padding = 0


class TabButtons(Horizontal):
    def __init__(self, ids: AppIds, buttons: tuple[TabLabel, ...]) -> None:
        self.buttons = buttons
        self.tab_ids = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield TabBtn(app_ids=self.tab_ids, label=btn_enum)

    def on_mount(self) -> None:
        self.query(TabBtn).first().add_class(Tcss.last_clicked_tab_btn)

    @on(TabBtn.Pressed)
    def update_tcss_classes(self, event: TabBtn.Pressed) -> None:
        for btn in self.query(TabBtn).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
