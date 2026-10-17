from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from rich.markup import escape
from textual import on, work
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible, Static

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.gui.common import widget_factory
from chezmoi_mousse.gui.common.actionables import PromptBtnGroup
from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    MainSectionLabel,
    SubSectionLabel,
)
from chezmoi_mousse.str_enums import (
    BtnLabel,
    ChezmoiPrompts,
    ColorVar,
    Tcss,
    WriteCmd,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult
    from textual.containers import (
        HorizontalGroup,
    )
    from textual.widgets import Label

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import (
        ReadCmd,
    )


__all__ = ["OperateModal"]


# Unanswered prompts quit chezmoi, so a forgotten modal can't leave it waiting forever
PROMPT_TIMEOUT_SECONDS = 120


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


class ShowCmDiff(VerticalGroup):
    def __init__(self, diff_txt: str = "") -> None:
        self.diff_txt = diff_txt
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{'Chezmoi diff'}[/]",
            collapsed=False,
        )

    def _collapsible_contents(self) -> list[Static]:
        if not self.diff_txt:
            return [Static("No diff to show")]
        widgets = widget_factory.diff_statics(self.diff_txt)
        return widgets


class ShowAnswerLabel(SubSectionLabel): ...


class GeneralInfoLabel(FlatSectionLabel): ...


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
                yield GeneralInfoLabel("Ready to run", markup=False)
            yield PromptBtnGroup(
                labels=(
                    ChezmoiPrompts.all.prompt_item,
                    ChezmoiPrompts.diff.prompt_item,
                    ChezmoiPrompts.edit.prompt_item,
                    ChezmoiPrompts.no.prompt_item,
                    ChezmoiPrompts.no_to_all.prompt_item,
                    ChezmoiPrompts.quit.prompt_item,
                    ChezmoiPrompts.yes.prompt_item,
                    self.op_btn.run_label,
                    BtnLabel.cancel,
                    BtnLabel.close,
                ),
            )

    def on_mount(self) -> None:
        self.paths_in_scope = self.query_exactly_one(PathsInScope)
        prompt_btn_group = self.query_exactly_one(PromptBtnGroup)
        self.prompt_buttons = prompt_btn_group.query(Button)
        self.general_info_label = self.query_exactly_one(GeneralInfoLabel)
        if self.affected_paths:
            for button in self.prompt_buttons:
                if button.label in (BtnLabel.cancel, self.op_btn.run_label):
                    button.display = True
        else:
            self.general_info_label.update("Sorry this is a no-op, nothing to do.")
            for button in self.prompt_buttons:
                button.display = button.label == BtnLabel.cancel.value

    def _create_cm_git_diff(self, text: str) -> None:
        container = self.query_exactly_one(ScrollableContainer)
        show_cm_diff = ShowCmDiff(text)
        container.mount(show_cm_diff, before=self.general_info_label)
        container.scroll_end()

    def _create_show_answer_label(self, text: str) -> None:
        container = self.query_exactly_one(ScrollableContainer)
        container.mount(ShowAnswerLabel(escape(text)), before=self.general_info_label)
        container.scroll_end()

    async def _await_user_choice(self, options: list[str]) -> str:
        """Shows the offered prompt options and pauses until a button is clicked."""
        offered = {
            prompt.prompt_item
            for prompt in ChezmoiPrompts
            if prompt.prompt_item in options
        }
        for button in self.prompt_buttons:
            button.display = str(button.label) in offered

        self._prompt_future = asyncio.get_running_loop().create_future()
        try:
            async with asyncio.timeout(PROMPT_TIMEOUT_SECONDS):
                return await self._prompt_future
        except TimeoutError:
            self.general_info_label.update(
                f"No reply within {PROMPT_TIMEOUT_SECONDS} seconds, quitting."
            )
            return ChezmoiPrompts.quit.reply
        finally:
            self._prompt_future = None

    @work
    async def _run_interactive(self) -> None:
        self.paths_in_scope.query_exactly_one(Collapsible).collapsed = True
        cmd_enum = self.btn_label_to_cmd[self.op_btn]
        gen = tchezmoi.run_chezmoi_interactive(cmd_enum, self.path_arg)

        response: str | None = None
        try:
            while True:
                event = await gen.asend(response)

                if event.is_prompt:
                    prompt_text = f"{event.prompt_question} ({'/'.join(event.data)})?"
                    self.general_info_label.update(prompt_text)

                    # Pause worker on asyncio.Future until UI button is pressed
                    response = await self._await_user_choice(event.data)
                    if response == ChezmoiPrompts.no.reply:
                        self._create_show_answer_label(f"{event.prompt_question}: no")
                    elif response == ChezmoiPrompts.yes.reply:
                        self._create_show_answer_label(f"{event.prompt_question}: yes")
                    elif response == ChezmoiPrompts.quit.reply:
                        self._create_show_answer_label("asked to quit the operation")
                elif response == ChezmoiPrompts.diff.reply:
                    lines_text = "\n".join(event.data) + "\n"
                    self._create_cm_git_diff(lines_text)
                    response = None
                else:
                    self.general_info_label.update("\n".join(event.data))
                    response = None

        except StopAsyncIteration:
            self.general_info_label.update("Process completed.")
            for button in self.prompt_buttons:
                button.display = button.label == BtnLabel.close
        finally:
            # on cancel/dismiss the worker is cancelled, this terminates chezmoi
            await gen.aclose()

    @on(Button.Pressed)
    def handle_prompt_btn_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        button_label = str(event.button.label)

        if button_label in (BtnLabel.cancel, BtnLabel.close):
            for worker in self.workers:
                worker.cancel()
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
