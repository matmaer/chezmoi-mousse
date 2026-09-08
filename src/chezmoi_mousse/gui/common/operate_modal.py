from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse import store
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.gui.common.components import (
    InfoStatic,
    MainSectionLabel,
    SubSectionLabel,
)
from chezmoi_mousse.named_tuples import RunCommandInfo
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    OpInfoString,
    Tcss,
    WriteCmd,
)

if TYPE_CHECKING:
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import AffectedPaths

__all__ = ["LoadingModal", "OperateModal"]


class LoadingModal(ModalScreen[None]):
    """
    A modal screen that displays a loading indicator and a label.
    The screen does not dismiss on its own, and must be dismissed by the parent screen.
    """

    label_text: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield (VerticalGroup(Label(LabelStr.loading), LoadingIndicator()))

    def watch_label_text(self, label_text: str) -> None:
        if self.label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)


class OperateInfo(Static):
    live_run: reactive[bool] = reactive(False)

    def __init__(self, btn_label: BtnLabel | None) -> None:
        self.btn_label = btn_label
        super().__init__(classes=Tcss.operate_info)

    def on_mount(self) -> None:
        if self.btn_label is None:
            return

        self.cmd_info_fields = self._get_cmd_info_fields(self.btn_label)
        self.border_title = self.cmd_info_fields.border_title
        self.border_subtitle = self.cmd_info_fields.border_subtitle
        self._update_review_info()

    def _update_review_info(self) -> None:
        info_lines: list[str] = []
        if self.live_run is False:
            info_lines.append(OpInfoString.dry_run_notice)
        else:
            info_lines.append(OpInfoString.live_run_notice)
        if self.btn_label is not BtnLabel.apply_run:
            if store.cfg.auto_add is True:
                info_lines.append(OpInfoString.auto_add)
            if store.cfg.auto_commit is True:
                info_lines.append(OpInfoString.auto_commit)
            if store.cfg.auto_push is True:
                info_lines.append(OpInfoString.auto_push)
        else:
            info_lines.append(OpInfoString.auto_settings_not_applicable)
        info_lines.append(self.cmd_info_fields.cmd_description)
        self.update("\n".join(info_lines))

    def watch_live_run(self) -> None:
        if not self.display:
            return
        self._update_review_info()

    def _get_cmd_info_fields(self, btn_label: BtnLabel) -> RunCommandInfo:
        if btn_label is BtnLabel.add_run:
            return RunCommandInfo(
                border_title=BtnLabel.add_run,
                border_subtitle=OpInfoString.add_subtitle,
                cmd_description=OpInfoString.add_path_info,
            )
        elif btn_label is BtnLabel.apply_run:
            return RunCommandInfo(
                border_title=BtnLabel.apply_run,
                border_subtitle=OpInfoString.apply_subtitle,
                cmd_description=OpInfoString.apply_path_info,
            )
        elif btn_label is BtnLabel.destroy_run:
            return RunCommandInfo(
                border_title=BtnLabel.destroy_run,
                border_subtitle=OpInfoString.destroy_subtitle,
                cmd_description=OpInfoString.destroy_path_info,
            )
        elif btn_label is BtnLabel.forget_run:
            return RunCommandInfo(
                border_title=BtnLabel.forget_run,
                border_subtitle=OpInfoString.forget_subtitle,
                cmd_description=OpInfoString.forget_path_info,
            )
        elif btn_label is BtnLabel.re_add_run:
            return RunCommandInfo(
                border_title=BtnLabel.re_add_run,
                border_subtitle=OpInfoString.re_add_subtitle,
                cmd_description=OpInfoString.re_add_path_info,
            )
        else:
            raise ValueError(f"No run cmd info fields available for {btn_label}")


class ChangedPathsOutput(ScrollableContainer):
    class AddedManaged(Static): ...

    class RemovedManaged(Static): ...

    class ChangedStatus(Static): ...

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.changed_paths)
        yield SubSectionLabel(LabelStr.added_managed_paths)
        yield ChangedPathsOutput.AddedManaged(classes=Tcss.info)
        yield SubSectionLabel(LabelStr.removed_managed_paths)
        yield ChangedPathsOutput.RemovedManaged(classes=Tcss.info)
        yield SubSectionLabel(LabelStr.changed_status_paths)
        yield ChangedPathsOutput.ChangedStatus(classes=Tcss.info)
        yield SubSectionLabel(LabelStr.command_outputs)

    def on_mount(self) -> None:
        self.added_managed = self.query_exactly_one(self.AddedManaged)
        self.removed_managed = self.query_exactly_one(self.RemovedManaged)
        self.changed_status = self.query_exactly_one(self.ChangedStatus)
        if not store.changed.added_managed_str:
            self.added_managed.update("No added managed paths")
        if not store.changed.removed_managed_str:
            self.removed_managed.update("No removed managed paths")
        if not store.changed.changed_status_str:
            self.changed_status.update("No changed status paths")
        if store.changed.added_managed_str:
            self.added_managed.update(store.changed.added_managed_str)
        if store.changed.removed_managed_str:
            self.removed_managed.update(store.changed.removed_managed_str)
        if store.changed.changed_status_str:
            self.changed_status.update(store.changed.changed_status_str)


class AffectedPathsReview(ScrollableContainer):
    affected_paths: reactive[AffectedPaths | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.affected_paths)
        yield SubSectionLabel()
        yield InfoStatic()

    def on_mount(self) -> None:
        self.info_static = self.query_exactly_one(InfoStatic)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)

    def watch_affected_paths(self, affected_paths: AffectedPaths | None) -> None:
        if affected_paths is None:
            return
        self.sub_section_label.update(affected_paths.pretty_cmd)
        self.info_static.update(affected_paths.path_strings)


class OperateModal(ModalScreen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, *, labels: tuple[BtnLabel, ...]) -> None:
        self.operate_label = next(
            (label for label in labels if label in BtnLabel.run_btn_set()), None
        )
        self.labels = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield OperateInfo(self.operate_label)
            yield ChangedPathsOutput()
            yield AffectedPathsReview()

    def on_mount(self) -> None:
        operate_info = self.query_exactly_one(OperateInfo)
        changed_paths_output = self.query_exactly_one(ChangedPathsOutput)
        self.affected_paths_review = self.query_exactly_one(AffectedPathsReview)
        if len(self.labels) == 1 and self.labels[0] == BtnLabel.close:
            # condition after a refresh trees btn_label
            operate_info.display = False
            self.affected_paths_review.display = False
        elif self.operate_label is not None:
            changed_paths_output.display = False
            self._show_affected_paths()

    @work
    async def _show_affected_paths(self) -> None:
        if self.operate_label is None:
            return
        self.loading_modal = LoadingModal()
        await self.app.push_screen(self.loading_modal)
        self.loading_modal.label_text = LabelStr.get_affected_paths
        write_cmd = WriteCmd.get_write_cmd(self.operate_label)
        tab_path = store.get_tab_path(self.operate_label)
        if tab_path is None:
            tab_path = store.cfg.dest_dir
        result: AffectedPaths = await Commands.get_affected_paths(write_cmd, tab_path)
        self.affected_paths_review.affected_paths = result
        await self.loading_modal.dismiss()
