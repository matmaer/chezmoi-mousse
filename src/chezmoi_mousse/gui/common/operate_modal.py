from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from rich.markup import escape
from textual import on, work
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Collapsible, Static

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.asyncio_process_exec import ExecResult
from chezmoi_mousse.data_types import CommandResult
from chezmoi_mousse.gui.common import widget_factory
from chezmoi_mousse.gui.common.actionables import PromptBtnGroup
from chezmoi_mousse.gui.common.components import (
    CmdResultCollapsible,
    FlatSectionLabel,
    MainSectionLabel,
    SubSectionLabel,
    WarningLabel,
)
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import BtnLabel, ChezmoiPrompts, ColorVar, Tcss, WriteCmd

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult
    from textual.containers import HorizontalGroup
    from textual.widgets import Label

    from chezmoi_mousse.data_types import IterDirResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import ReadCmd


__all__ = ["OperateModal"]


PROMPT_TIMEOUT_SECONDS = 120  # timeout to revert to quit if a modal is forgotten


class PathsInScope(VerticalGroup):
    def __init__(self, read_cmd: ReadCmd, path_str: str, path_scope: str) -> None:
        self.read_cmd = read_cmd
        self.path_str = path_str
        self.path_scope = path_scope
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{'Paths in Scope'}[/]",
            collapsed=False,
        )

    def _collapsible_contents(self) -> list[Label | Static]:
        contents: list[Label | Static] = []
        pretty_cmd = f"{self.read_cmd.pretty_cmd} {self.path_str}".rstrip()
        contents.append(FlatSectionLabel(f"{escape(pretty_cmd)} (paths)"))
        contents.append(Static(self.path_scope, markup=False, classes=Tcss.cmd_output))
        return contents


class CmGitConfig(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{'Chezmoi git config'}[/]",
        )

    def _collapsible_contents(self) -> list[HorizontalGroup]:
        truth_dict: dict[str, bool] = {}
        truth_dict["autoadd enabled"] = store.cfg.auto_add
        truth_dict["autocommit enabled"] = store.cfg.auto_commit
        truth_dict["autopush enabled"] = store.cfg.auto_push
        widgets = widget_factory.truth_widgets(truth_dict)
        return widgets


class SelectPaths(VerticalGroup):
    def __init__(self, dir_path: Path) -> None:
        self.dir_path = dir_path
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{'Select additional paths'}[/]",
            collapsed=False,
        )

    def _collapsible_contents(self) -> list[Checkbox]:
        widgets: list[Checkbox] = [
            Checkbox("Select all directories", classes=Tcss.select_all)
        ]
        dir_children: IterDirResult = path_funcs.get_un_man_children(self.dir_path)
        if dir_children.error:
            self.notify(f"dir children has error {dir_children.error}")
        for path in dir_children.dirs:
            widgets.append(Checkbox(str(path)))
        widgets.append(Checkbox("Select all files", classes=Tcss.select_all))
        for path in dir_children.files:
            widgets.append(Checkbox(str(path)))
        return widgets


class ShowCmDiff(VerticalGroup):
    def __init__(self, diff_txt: str = "", diff_title: str = "") -> None:
        self.diff_txt = diff_txt
        self.diff_title = diff_title
        super().__init__()

    def compose(self) -> ComposeResult:
        title = (
            f"Chezmoi diff: {self.diff_title}" if self.diff_title else "Chezmoi diff"
        )
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{escape(title)}[/]",
            collapsed=False,
        )

    def _collapsible_contents(self) -> list[Static]:
        if not self.diff_txt:
            return [Static("No diff to show")]
        widgets = widget_factory.diff_statics(self.diff_txt)
        return widgets


class _GeneralInfoLabel(MainSectionLabel): ...


class OperateModal(ModalScreen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    btn_label_to_cmd: ClassVar[dict[str, WriteCmd]] = {
        BtnLabel.chezmoi_add: WriteCmd.add,
        BtnLabel.chezmoi_apply: WriteCmd.apply,
        BtnLabel.chezmoi_destroy: WriteCmd.destroy,
        BtnLabel.chezmoi_forget: WriteCmd.forget,
        BtnLabel.chezmoi_re_add: WriteCmd.re_add,
    }

    def __init__(self, op_btn: BtnLabel, path: Path, affected_paths: str) -> None:
        self.op_btn: BtnLabel = op_btn
        self.path = path
        self.path_str: str = "" if path == store.cfg.dest_dir else str(path)
        self.path_arg: Path | None = None if path == store.cfg.dest_dir else path
        self.affected_paths = affected_paths
        self._prompt_future: asyncio.Future[str] | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield MainSectionLabel(f"{self.op_btn.value} {self.path_str}".rstrip())
            with ScrollableContainer():
                yield CmGitConfig()
                yield PathsInScope(
                    self.op_btn.dry_cmd, self.path_str, self.affected_paths
                )
                if self.op_btn == BtnLabel.chezmoi_add and self.path.is_dir():
                    yield SelectPaths(self.path)
                yield _GeneralInfoLabel("Ready to run", markup=False)
            yield PromptBtnGroup(
                labels=(
                    ChezmoiPrompts.diff.prompt_item,
                    ChezmoiPrompts.yes.prompt_item,
                    ChezmoiPrompts.no.prompt_item,
                    ChezmoiPrompts.no_to_all.prompt_item,
                    ChezmoiPrompts.edit.prompt_item,
                    ChezmoiPrompts.all.prompt_item,
                    ChezmoiPrompts.quit.prompt_item,
                    self.op_btn.run_label,
                    BtnLabel.cancel,
                    BtnLabel.close,
                )
            )

    def on_mount(self) -> None:
        self.paths_in_scope = self.query_exactly_one(PathsInScope)
        prompt_btn_group = self.query_exactly_one(PromptBtnGroup)
        self.prompt_buttons = prompt_btn_group.query(Button)
        self.general_info_label = self.query_exactly_one(_GeneralInfoLabel)
        if self.affected_paths:
            for button in self.prompt_buttons:
                if button.label in (BtnLabel.cancel, self.op_btn.run_label):
                    button.display = True
        else:
            self.general_info_label.update("Sorry this is a no-op, nothing to do.")
            for button in self.prompt_buttons:
                button.display = button.label == BtnLabel.cancel.value

    def _create_cm_git_diff(self, text: str, title: str) -> ShowCmDiff:
        container = self.query_exactly_one(ScrollableContainer)
        show_cm_diff = ShowCmDiff(text, title)
        container.mount(show_cm_diff, before=self.general_info_label)
        container.scroll_end()
        return show_cm_diff

    def _create_warning_label(self, text: str) -> None:
        container = self.query_exactly_one(ScrollableContainer)
        before = self.general_info_label
        container.mount(WarningLabel(escape(text)), before=before)

    def _create_green_label(self, text: str) -> None:
        container = self.query_exactly_one(ScrollableContainer)
        before = self.general_info_label
        container.mount(SubSectionLabel(escape(text)), before=before)

    def _create_cmd_result(self, exec_result: ExecResult) -> None:
        cmd_enum = self.btn_label_to_cmd[self.op_btn]
        args = (*cmd_enum.value, *([str(self.path_arg)] if self.path_arg else []))
        result = CommandResult(
            cmd_enum=cmd_enum,
            full_cmd=f"chezmoi {' '.join(args)}",
            pretty_cmd=tchezmoi.pretty_cmd(cmd_enum, self.path_arg),
            returncode=exec_result.returncode,
            std_err=exec_result.std_err,
            std_out=exec_result.std_out,
            out_list=exec_result.std_out.splitlines(),
            time_stamp=datetime.now().strftime("%H:%M:%S"),
            interactive_approved=exec_result.interactive_approved,
        )
        container = self.query_exactly_one(ScrollableContainer)
        container.mount(CmdResultCollapsible(cmd_result=result))
        container.scroll_end()
        # same routing as tchezmoi._exec_chezmoi so the Logs tab shows the result
        self.app.app_log.cmd_result = result
        self.app.cmd_log.cmd_result = result
        self.app.post_message(CommandResultMsg(result))

    async def _await_user_choice(self, options: list[str]) -> str:
        """Shows the offered prompt options and pauses until a button is clicked."""
        offered = set(options)
        for button in self.prompt_buttons:
            button.display = str(button.label) in offered
            button.disabled = False

        self._prompt_future = asyncio.get_running_loop().create_future()
        try:
            async with asyncio.timeout(PROMPT_TIMEOUT_SECONDS):
                return await self._prompt_future
        except TimeoutError:
            self._create_warning_label(
                f"No reply within {PROMPT_TIMEOUT_SECONDS} seconds, quitting."
            )
            return ChezmoiPrompts.quit.reply
        finally:
            self._prompt_future = None
            # chezmoi is busy again, nothing can be answered until the next prompt
            for button in self.prompt_buttons:
                button.disabled = True

    @work
    async def _run_interactive(self) -> None:
        # Pressing diff again for the same prompt toggles the existing diff
        last_diff: ShowCmDiff | None = None
        pending_diff_question: str | None = None

        async def handle_prompt(prompt_question: str, options: list[str]) -> str:
            nonlocal last_diff, pending_diff_question

            self.general_info_label.update(f"{prompt_question} ({'/'.join(options)})?")
            response = await self._await_user_choice(options)
            while (
                response == ChezmoiPrompts.diff.reply
                and last_diff is not None
                and prompt_question == last_diff.diff_title
            ):
                collapsible = last_diff.query_exactly_one(Collapsible)
                collapsible.collapsed = not collapsible.collapsed
                if not collapsible.collapsed:
                    last_diff.scroll_visible()
                response = await self._await_user_choice(options)

            if response == ChezmoiPrompts.no.reply:
                self._create_warning_label(f"{prompt_question}: NO")
            elif response == ChezmoiPrompts.yes.reply:
                self._create_green_label(f"{prompt_question}: YES")
            elif response == ChezmoiPrompts.quit.reply:
                self._create_green_label("Asked to quit the operation")

            pending_diff_question = (
                prompt_question if response == ChezmoiPrompts.diff.reply else None
            )
            return response

        events = tchezmoi.run_chezmoi_interactive(
            self.btn_label_to_cmd[self.op_btn], self.path_arg, handle_prompt
        )
        try:
            async for event in events:
                if isinstance(event, ExecResult):
                    self._create_cmd_result(event)
                    self.general_info_label.update(
                        "Process completed."
                        if event.returncode == 0
                        else f"Process exit, returncode {event.returncode})."
                    )
                    self.app.run_worker(
                        self.app.left_side.refresh_trees(),
                        name="refresh_trees_after_operation",
                    )
                elif pending_diff_question is not None:
                    self.paths_in_scope.query_exactly_one(Collapsible).collapsed = True
                    last_diff = self._create_cm_git_diff(
                        "\n".join(event) + "\n", pending_diff_question
                    )
                    pending_diff_question = None
            for button in self.prompt_buttons:
                button.display = button.label == BtnLabel.close
                button.disabled = False
        finally:
            # on cancel/dismiss the worker is cancelled, this terminates chezmoi
            await events.aclose()

    @on(Button.Pressed)
    def handle_prompt_btn_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        button_label = str(event.button.label)

        if button_label in (BtnLabel.cancel, BtnLabel.close):
            self.dismiss()
        elif button_label == self.op_btn.run_label:
            for button in self.prompt_buttons:
                button.display = False
            self._run_interactive()
        elif self._prompt_future is not None and not self._prompt_future.done():
            for prompt in ChezmoiPrompts:
                if prompt.prompt_item == button_label:
                    self._prompt_future.set_result(prompt.reply)
                    break
