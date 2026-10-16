from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from rich.markup import escape
from textual import on, work
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible, Static

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.gui.common.actionables import PromptBtnGroup
from chezmoi_mousse.gui.common.components import FlatSectionLabel, SubSectionLabel
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Chars,
    ChezmoiPrompts,
    ColorVar,
    WriteCmd,
)

if TYPE_CHECKING:
    from pathlib import Path

    from rich.text import Text
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import (
        ReadCmd,
    )


__all__ = ["OperateModal"]


# Unanswered prompts quit chezmoi, so a forgotten modal can't leave it waiting forever
PROMPT_TIMEOUT_SECONDS = 120


class AffectedPathsStatic(Static): ...


class AffectedPaths(Collapsible):
    def __init__(
        self, *, read_cmd: ReadCmd, path: Path | None, highlighted_paths: Text
    ) -> None:
        super().__init__(
            ScrollableContainer(Static(highlighted_paths, markup=False)),
            title=self._colored_title(read_cmd, path),
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
        )

    def _colored_title(self, read_cmd: ReadCmd, path: Path | None) -> str:
        color = f"${ColorVar.text_success}"
        rel_path = "" if path is None else path_funcs.get_rel_path_str(path)
        pretty_cmd = f"{read_cmd.pretty_cmd} {rel_path}".rstrip()
        return f"[{color}]{escape(pretty_cmd)}[/]"


class InteractiveOutputStatic(Static): ...


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

    def __init__(self, op_btn: BtnLabel, path: Path, affected_paths: Text) -> None:
        self.op_btn = op_btn
        self.path = path
        self.affected_paths = affected_paths
        self._prompt_future: asyncio.Future[str] | None = None
        self._output_buffer = ""
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield SubSectionLabel(
                f"autoadd enabled: {store.cfg.auto_add}, autocommit enabled: "
                f"{store.cfg.auto_commit}, autopush enabled: {store.cfg.auto_push}"
            )
            yield FlatSectionLabel()
            yield AffectedPathsStatic(markup=False)
            yield InteractiveOutputStatic(markup=False)
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
        prompt_btn_group = self.query_exactly_one(PromptBtnGroup)
        self.prompt_buttons = prompt_btn_group.query(Button)
        self.affected_static = self.query_exactly_one(AffectedPathsStatic)
        if self.affected_paths:
            self.affected_static.update(self.affected_paths)
            for button in self.prompt_buttons:
                if button.label in (BtnLabel.cancel, self.op_btn.run_label):
                    button.display = True
        else:
            self.affected_static.update("Sorry this is a no-op, nothing to do.")
            for button in self.prompt_buttons:
                button.display = button.label == BtnLabel.cancel.value
        self.interactive_output_static = self.query_exactly_one(InteractiveOutputStatic)
        self.interactive_output_static.display = False

    def _append_output(self, text: str) -> None:
        """Appends output text to InteractiveOutputStatic."""
        self._output_buffer += text
        self.interactive_output_static.update(self._output_buffer)

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
            self._append_output(
                f"\nNo reply within {PROMPT_TIMEOUT_SECONDS} seconds, quitting.\n"
            )
            return ChezmoiPrompts.quit.reply
        finally:
            self._prompt_future = None

    @work
    async def _run_interactive(self) -> None:
        self.affected_static.display = False
        self.interactive_output_static.display = True

        cmd_enum = self.btn_label_to_cmd[self.op_btn]
        gen = tchezmoi.run_chezmoi_interactive(cmd_enum, self.path)

        response: str | None = None
        try:
            while True:
                event = await gen.asend(response)

                if event.is_prompt:
                    prompt_text = f"\nPrompt options: {' / '.join(event.data)}\n"
                    self._append_output(prompt_text)

                    # Pause worker on asyncio.Future until UI button is pressed
                    response = await self._await_user_choice(event.data)
                else:
                    lines_text = "\n".join(event.data) + "\n"
                    self._append_output(lines_text)
                    response = None

        except StopAsyncIteration:
            self._append_output("\nProcess completed.")
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
