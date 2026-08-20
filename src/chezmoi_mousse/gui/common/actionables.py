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
    BindingDescription,
    FlatBtnLabel,
    OpBtnLabel,
    OpInfoString,
    TabLabel,
    Tcss,
    WriteCmd,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.cm_types import ReviewBtnDict, RunBtnDict
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = [
    "DirContentBtn",
    "FlatButton",
    "FlatButtonsVertical",
    "RefreshTreeButton",
    "ReviewBtnGroup",
    "ReviewButton",
    "RunButton",
    "RunBtnGroup",
    "SwitchSlider",
    "TabButton",
    "TabButtons",
]


class ExitOpModalBtn(Button):
    def __init__(self) -> None:
        super().__init__(
            classes=Tcss.operate_button,
            label=OpBtnLabel.cancel,
        )


class ToggleDryRunBtn(Button):
    def __init__(self) -> None:
        super().__init__(
            classes=Tcss.operate_button,
            label="not set",
        )


class DirContentBtn(Button):
    def __init__(self, *, label: str, path: Path, app_ids: AppIds) -> None:
        super().__init__(label=label)
        self.path = path
        self.app_ids = app_ids


class FlatButton(Button):
    def __init__(self, ids: AppIds, *, btn_label: FlatBtnLabel) -> None:
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=ids.flat_button_id(btn=btn_label),
            label=btn_label,
            variant="primary",
        )


class FlatButtonsVertical(Vertical):
    def __init__(self, ids: AppIds, *, labels: tuple[FlatBtnLabel, ...]) -> None:
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.labels: tuple[FlatBtnLabel, ...] = labels

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield FlatButton(self.ids, btn_label=label)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatButton.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatButton.Pressed) -> None:
        for btn in self.query(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class RefreshTreeButton(Button):
    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        super().__init__(
            classes=Tcss.refresh_button,
            id=self.app_ids.op_btn.refresh_tree,
            label=OpBtnLabel.refresh_trees,
        )


class ReviewButton(Button):
    def __init__(
        self, app_ids: AppIds, btn_label: OpBtnLabel, btn_data: ReviewBtnData
    ) -> None:
        self.app_ids = app_ids
        self.bd = btn_data
        super().__init__(
            classes=Tcss.operate_button, id=btn_data.btn_id, label=btn_label
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
            yield ReviewButton(self.app_ids, btn_label=btn_label, btn_data=btn_data)

    def set_path_arg(self, path: Path) -> None:
        buttons = self.query_children(ReviewButton)
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


class RunButton(Button):
    def __init__(self, btn_label: OpBtnLabel, btn_data: RunBtnData) -> None:
        self.bd = btn_data
        super().__init__(
            classes=Tcss.operate_button, id=btn_data.btn_id, label=btn_label
        )


class RunBtnGroup(HorizontalGroup):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, btn_pressed: ReviewButton | None) -> None:
        self.btn = btn_pressed
        super().__init__(
            classes=Tcss.op_btn_group,
        )

    def on_mount(self) -> None:
        if isinstance(self.btn, ReviewButton):
            self.run_buttons: RunBtnDict = self._get_run_buttons(self.btn.app_ids)
            for btn_label, btn_data in self.run_buttons.items():
                self.mount(RunButton(btn_label=btn_label, btn_data=btn_data))
            self.mount(ExitOpModalBtn())
        else:
            self.mount(ExitOpModalBtn())
            # TODO: update via reactive label to 'refresh trees' if there were changes
            self.query_exactly_one(ExitOpModalBtn).label = OpBtnLabel.close
        self.mount(ToggleDryRunBtn())
        self._set_toggle_dry_run_btn_label(self.app.cmattr.dry_run)

    def _set_toggle_dry_run_btn_label(self, dry_run: bool) -> None:
        btn = self.query_exactly_one(ToggleDryRunBtn)
        btn.label = (
            BindingDescription.add_dry_run
            if dry_run is False
            else BindingDescription.remove_dry_run
        )

    def update_run_buttons_after_run_command(self, changes: bool) -> None:
        for btn in self.query_children(RunButton):
            btn.disabled = True
        if changes:
            self.query_exactly_one(ExitOpModalBtn).label = OpBtnLabel.refresh_trees
        else:
            self.query_exactly_one(ExitOpModalBtn).label = OpBtnLabel.close

    def _get_run_buttons(self, app_ids: AppIds) -> RunBtnDict:
        if app_ids.tab_label == TabLabel.add:
            add_run_data = RunBtnData(
                btn_id=app_ids.op_btn.add_run,
                btn_qid=app_ids.op_btn.add_run_q,
            )
            return {
                OpBtnLabel.add_run: add_run_data,
            }
        forget_run_data = RunBtnData(
            btn_id=app_ids.op_btn.forget_run,
            btn_qid=app_ids.op_btn.forget_run_q,
        )
        destroy_run_data = RunBtnData(
            btn_id=app_ids.op_btn.destroy_run,
            btn_qid=app_ids.op_btn.destroy_run_q,
        )
        _forget_destroy_buttons = {
            OpBtnLabel.forget_run: forget_run_data,
            OpBtnLabel.destroy_run: destroy_run_data,
        }
        if app_ids.tab_label == TabLabel.apply:
            apply_run_data = RunBtnData(
                btn_id=app_ids.op_btn.apply_run,
                btn_qid=app_ids.op_btn.apply_run_q,
            )
            return {
                OpBtnLabel.apply_run: apply_run_data,
                **_forget_destroy_buttons,
            }
        elif app_ids.tab_label == TabLabel.re_add:
            op_btn_data = RunBtnData(
                btn_id=app_ids.op_btn.re_add_run,
                btn_qid=app_ids.op_btn.re_add_run_q,
            )
            return {OpBtnLabel.re_add_run: op_btn_data, **_forget_destroy_buttons}
        else:
            raise ValueError(f"Unexpected tab_label {app_ids.tab_label}")

    @on(ToggleDryRunBtn.Pressed)
    def handle_toggle_dry_run_pressed(self, event: ToggleDryRunBtn.Pressed) -> None:
        if (
            self.app.cmattr.dry_run
            and event.button.label != BindingDescription.remove_dry_run
        ):
            self.notify("dry run out of sync", severity="error")
        self.app.cmattr.dry_run = not self.app.cmattr.dry_run
        self._set_toggle_dry_run_btn_label(self.app.cmattr.dry_run)


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


class TabButton(Button):
    def __init__(self, *, app_ids: AppIds, label: TabLabel) -> None:
        super().__init__(classes=Tcss.tab_button, label=label)
        self.app_ids = app_ids


class TabButtons(Horizontal):
    def __init__(self, ids: AppIds, buttons: tuple[TabLabel, ...]) -> None:
        self.buttons = buttons
        self.tab_ids = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield TabButton(app_ids=self.tab_ids, label=btn_enum)

    def on_mount(self) -> None:
        self.query(TabButton).first().add_class(Tcss.last_clicked_tab_btn)

    @on(TabButton.Pressed)
    def update_tcss_classes(self, event: TabButton.Pressed) -> None:
        for btn in self.query(TabButton).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
