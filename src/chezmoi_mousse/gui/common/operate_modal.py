from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from rich.markup import escape
from textual import on, work
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Collapsible, Static

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.data_types import CommandResult, ExecResult
from chezmoi_mousse.gui.common import widget_factory
from chezmoi_mousse.gui.common.actionables import PromptBtnGroup
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.str_enums import BtnLabel, ChezmoiPrompts, ColorVar, LabelStr, Tcss

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult
    from textual.containers import HorizontalGroup

    from chezmoi_mousse.data_types import IterDirResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.str_enums import ReadCmd


__all__ = ["OperateModal"]

PROMPT_TIMEOUT = 120  # timeout to revert to quit if a modal is forgotten
BUSY_POLL_INTERVAL = 0.05  # quick interval to check for toggling the loading reactive
LOADING_START_DELAY = 0.15  # delay when the loading indicator should start showing
LOADING_STOP_DELAY = 0.3  # delay when the loading indicator should stop showing


class PathsInScope(VerticalGroup):
    def __init__(self, read_cmd: ReadCmd, path_str: str, path_scope: str) -> None:
        self.read_cmd = read_cmd
        self.path_str = path_str
        self.path_scope = path_scope
        self.pretty_cmd = f"{self.read_cmd.pretty_cmd} {self.path_str} (paths)"
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Collapsible(
            *(
                Static(f"{self.pretty_cmd}", markup=False, classes=Tcss.blue_label),
                Static(self.path_scope, markup=False, classes=Tcss.cmd_output),
            ),
            title=f"[${ColorVar.text_success}]{'Paths in Scope'}[/]",
            collapsed=False,
        )


class CmGitConfig(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{'Chezmoi git config'}[/]",
        )

    def _collapsible_contents(self) -> list[HorizontalGroup]:
        return [
            widget_factory.truth_widget(label, truth)
            for label, truth in zip(
                ["autoadd", "autocommit", "autopush"],
                [store.cfg.auto_add, store.cfg.auto_commit, store.cfg.auto_push],
                strict=True,
            )
        ]


class SelectPaths(VerticalGroup):
    def __init__(self, dir_path: Path) -> None:
        self.dir_path = dir_path
        self._checkbox_paths: dict[Checkbox, Path] = {}
        self._select_all_sections: dict[Checkbox, list[Checkbox]] = {}
        super().__init__()

    @property
    def selected_paths(self) -> list[Path]:
        return path_funcs.sort_paths(
            path for checkbox, path in self._checkbox_paths.items() if checkbox.value
        )

    def compose(self) -> ComposeResult:
        yield Collapsible(
            *self._collapsible_contents(),
            title=f"[${ColorVar.text_success}]{'Select additional paths'}[/]",
            collapsed=False,
        )

    def _path_checkbox(self, path: Path) -> Checkbox:
        checkbox = Checkbox(str(path))
        self._checkbox_paths[checkbox] = path
        return checkbox

    def _section(self, select_all_label: str, paths: Iterable[Path]) -> list[Checkbox]:
        select_all = Checkbox(select_all_label, classes=Tcss.select_all)
        path_checkboxes = [self._path_checkbox(path) for path in paths]
        self._select_all_sections[select_all] = path_checkboxes
        return [select_all, *path_checkboxes]

    def _collapsible_contents(self) -> list[Checkbox]:
        dir_children: IterDirResult = path_funcs.get_un_man_children(self.dir_path)
        if dir_children.error:
            self.notify(f"dir children has error {dir_children.error}")
        check_box_list: list[Checkbox] = []
        if dir_children.dirs:
            check_box_list.extend(
                self._section("Select all directories", dir_children.dirs)
            )
        if dir_children.files:
            check_box_list.extend(self._section("Select all files", dir_children.files))
        return check_box_list

    @on(Checkbox.Changed)
    def _apply_select_all(self, event: Checkbox.Changed) -> None:
        section = self._select_all_sections.get(event.checkbox)
        if section is None:
            return
        for checkbox in section:
            checkbox.value = event.value


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
        widgets = widget_factory.diff_lines(self.diff_txt)
        return widgets


class OperateModal(ModalScreen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, *, op_btn: BtnLabel, op_path: Path, affected_paths: str) -> None:
        self.op_btn: BtnLabel = op_btn
        self.op_path = op_path
        self.path_str: str = "" if op_path == store.cfg.dest_dir else str(op_path)
        self.path_arg: Path | None = None if op_path == store.cfg.dest_dir else op_path
        self.affected_paths = affected_paths
        self.busy: bool = False
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                f"{self.op_btn.value} {self.path_str}".rstrip(),
                markup=False,
                classes=Tcss.main_label,
            )
            with ScrollableContainer():
                yield CmGitConfig()
                yield PathsInScope(
                    self.op_btn.dry_cmd, self.path_str, self.affected_paths
                )
            yield Static(LabelStr.ready_to_run, classes=Tcss.main_label)
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
        self.prompt_future: asyncio.Future[str] | None = None
        self.answers = self.query_exactly_one(ScrollableContainer)
        if self.op_btn == BtnLabel.chezmoi_add and self.op_path.is_dir():
            self.answers.mount(SelectPaths(self.op_path))
        self.paths_in_scope = self.query_exactly_one(PathsInScope)
        self.prompt_btn_group = self.query_exactly_one(PromptBtnGroup)
        self.prompt_buttons = self.prompt_btn_group.query(Button)
        self.general_info_label = self.query_one(Tcss.main_label.q, Static)
        for button in self.prompt_buttons:
            if button.label in (BtnLabel.cancel, self.op_btn.run_label):
                button.display = True
        self.loading_timer = self.set_interval(
            interval=BUSY_POLL_INTERVAL, callback=self._check_busy
        )

    async def _check_busy(self) -> None:
        if not self.busy and self.prompt_btn_group.loading:
            await asyncio.sleep(LOADING_STOP_DELAY)
        elif self.busy and not self.prompt_btn_group.loading:
            await asyncio.sleep(LOADING_START_DELAY)
        self.prompt_btn_group.loading = self.busy

    def _create_cm_git_diff(self, text: str, title: str) -> ShowCmDiff:
        container = self.query_exactly_one(ScrollableContainer)
        show_cm_diff = ShowCmDiff(text, title)
        container.mount(show_cm_diff)
        return show_cm_diff

    def _handle_cmd_result(self, result: CommandResult) -> None:
        container = self.query_exactly_one(ScrollableContainer)
        container.mount(widget_factory.cmd_result_collapsible(cmd_result=result))
        # same routing as tchezmoi._exec_chezmoi so the Logs tab shows the result
        self.app.logs_tab.cmd_result = result
        self.app.post_message(CommandResultMsg(result))
        self.general_info_label.update(
            "Process completed."
            if result.returncode == 0
            else f"Process exit, returncode {result.returncode})."
        )
        self.app.operate_tab.refresh_trees()

    async def _await_user_choice(self, options: list[str]) -> str:
        """Shows the offered prompt options and pauses until a button is clicked."""
        self.busy = False
        offered = set(options)
        for button in self.prompt_buttons:
            button.display = str(button.label) in offered
            button.disabled = False

        self.prompt_future = asyncio.get_running_loop().create_future()
        try:
            async with asyncio.timeout(PROMPT_TIMEOUT):
                return await self.prompt_future
        except TimeoutError:
            self.answers.mount(
                Static(
                    f"No reply within {PROMPT_TIMEOUT} seconds, quitting.",
                    classes=Tcss.green_label,
                )
            )
            return ChezmoiPrompts.quit.reply
        finally:
            self.prompt_future = None
            # chezmoi is busy again, nothing can be answered until the next prompt
            for button in self.prompt_buttons:
                button.disabled = True
            self.busy = True

    @work
    async def _run_interactive(self) -> None:
        last_diff: ShowCmDiff | None = None
        pending_diff_question: str | None = None

        async def handle_prompt(prompt_question: str, options: list[str]) -> str:
            nonlocal last_diff, pending_diff_question

            self.general_info_label.update(f"{prompt_question} ({'/'.join(options)})?")
            response = await self._await_user_choice(options)
            # Pressing diff again for the same prompt toggles the existing diff
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
                self.answers.mount(widget_factory.truth_widget(prompt_question, False))
            elif response == ChezmoiPrompts.yes.reply:
                self.answers.mount(widget_factory.truth_widget(prompt_question, True))
            elif response == ChezmoiPrompts.quit.reply:
                self.answers.mount(Static(LabelStr.quit_op, classes=Tcss.green_label))

            pending_diff_question = (
                prompt_question if response == ChezmoiPrompts.diff.reply else None
            )
            return response

        verb_arg: Path | list[str] | None = self.path_arg
        pretty_verb_arg: Path | str | None = self.path_arg
        for select_paths in self.query(SelectPaths):
            select_paths.disabled = True
            if selected := select_paths.selected_paths:
                all_paths = [self.op_path, *selected]
                verb_arg = [str(path) for path in all_paths]
                pretty_verb_arg = " ".join(
                    path_funcs.get_rel_path_str(path) for path in all_paths
                )

        events = tchezmoi.run_chezmoi_interactive(
            self.op_btn.write_cmd, verb_arg, handle_prompt
        )
        self.busy = True
        try:
            async for event in events:
                if isinstance(event, ExecResult):
                    result = CommandResult(
                        cmd_enum=event.cmd_enum,
                        full_cmd=event.full_cmd,
                        pretty_cmd=tchezmoi.pretty_cmd(event.cmd_enum, pretty_verb_arg),
                        returncode=event.returncode,
                        std_err=event.std_err,
                        std_out=event.std_out,
                        time_stamp=event.time_stamp,
                        interactive_approved=event.interactive_approved,
                    )
                    self._handle_cmd_result(result)

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
            self.busy = False
            # if the loop exits early (e.g. an exception), stop chezmoi gracefully
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
        elif self.prompt_future is not None and not self.prompt_future.done():
            for prompt in ChezmoiPrompts:
                if prompt.prompt_item == button_label:
                    self.prompt_future.set_result(prompt.reply)
                    break
