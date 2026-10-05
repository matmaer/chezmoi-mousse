from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from textual import on, work
from textual.containers import (
    Horizontal,
    Vertical,
)
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    RadioButton,
    RadioSet,
    Static,
    TabPane,
    Tree,
)

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.data_types import NodeData
from chezmoi_mousse.gui.common.actionables import (
    OperateBtnGroup,
    PromptBtnGroup,
    SwitchGroup,
)
from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    MainSectionLabel,
    PathInfo,
    SubSectionLabel,
)
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.common.operate_views import (
    ContentView,
    DiffReverseView,
    DiffView,
    GitLogView,
)
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Chars,
    ChezmoiPrompts,
    LabelStr,
    Tcss,
    TreeName,
    WriteCmd,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["OperateTab"]


# Unanswered prompts quit chezmoi, so a forgotten modal can't leave it waiting forever
PROMPT_TIMEOUT_SECONDS = 120


class AffectedPathsStatic(Static): ...


class InteractiveOutputStatic(Static): ...


class ChezmoiCmdModal(ModalScreen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    btn_label_to_cmd: ClassVar[dict[str, WriteCmd]] = {
        BtnLabel.chezmoi_add: WriteCmd.add,
        BtnLabel.chezmoi_apply: WriteCmd.apply,
        BtnLabel.chezmoi_destroy: WriteCmd.destroy,
        BtnLabel.chezmoi_forget: WriteCmd.forget,
        BtnLabel.chezmoi_re_add: WriteCmd.re_add,
    }
    btn_label_to_dry_cmd: ClassVar[dict[str, WriteCmd]] = {
        BtnLabel.chezmoi_add: WriteCmd.dry_add,
        BtnLabel.chezmoi_apply: WriteCmd.dry_apply,
        BtnLabel.chezmoi_destroy: WriteCmd.dry_destroy,
        BtnLabel.chezmoi_forget: WriteCmd.dry_forget,
        BtnLabel.chezmoi_re_add: WriteCmd.dry_re_add,
    }

    def __init__(self, btn_label: str, path: Path) -> None:
        self.btn_label = btn_label
        self.path = path
        self._prompt_future: asyncio.Future[str] | None = None
        self._output_buffer = ""
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield SubSectionLabel(
                f"autoadd enabled: {store.cfg.auto_add}, autocommit enabled: "
                f"{store.cfg.auto_commit}, autopush enabled: {store.cfg.auto_push}"
            )
            yield FlatSectionLabel(f"{self.btn_label} Command")
            yield AffectedPathsStatic()
            yield InteractiveOutputStatic()
            yield PromptBtnGroup(
                labels=(
                    ChezmoiPrompts.all.btn_label,
                    ChezmoiPrompts.diff.btn_label,
                    ChezmoiPrompts.edit.btn_label,
                    ChezmoiPrompts.no.btn_label,
                    ChezmoiPrompts.no_to_all.btn_label,
                    ChezmoiPrompts.quit.btn_label,
                    ChezmoiPrompts.yes.btn_label,
                    BtnLabel.cancel,
                    BtnLabel.close,
                ),
            )

    def on_mount(self) -> None:
        prompt_btn_group = self.query_exactly_one(PromptBtnGroup)
        self.run_label = f"Run interactive {self.btn_label}"
        prompt_btn_group.mount(
            Button(label=self.run_label, classes=Tcss.prompt_button), before=0
        )
        self.prompt_buttons = prompt_btn_group.query(Button)
        for button in self.prompt_buttons:
            if button.label == BtnLabel.cancel or button.label == self.run_label:
                continue
            button.display = False
        self.affected_paths_static = self.query_exactly_one(AffectedPathsStatic)
        self.interactive_output_static = self.query_exactly_one(InteractiveOutputStatic)
        self.interactive_output_static.display = False
        self._run_affected_paths()

    @work
    async def _run_affected_paths(self) -> None:
        # set flat section label with the dry run command
        flat_section_label = self.query_exactly_one(FlatSectionLabel)
        flat_section_label.update(
            f"{self.btn_label_to_dry_cmd[self.btn_label].pretty_cmd} {self.path}"
        )
        # run the command
        dry_cmd = self.btn_label_to_dry_cmd[self.btn_label]
        affected_paths_cr: list[Path] = await tchezmoi.get_affected_paths(
            self.app, dry_cmd, self.path
        )
        self.affected_paths_static.update("\n".join(str(p) for p in affected_paths_cr))

    def _append_output(self, text: str) -> None:
        """Appends output text to InteractiveOutputStatic."""
        self._output_buffer += text
        self.interactive_output_static.update(self._output_buffer)

    async def _await_user_choice(self, options: list[str]) -> str:
        """Shows the offered prompt options and pauses until a button is clicked."""
        offered = {
            prompt.btn_label
            for prompt in ChezmoiPrompts
            if prompt.prompt_item in options
        }
        for button in self.prompt_buttons:
            button.display = str(button.label) in offered | {BtnLabel.close}

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
            for button in self.prompt_buttons:
                if button.label != BtnLabel.close:
                    button.display = False

    @work
    async def _run_interactive(self) -> None:
        self.affected_paths_static.display = False
        self.interactive_output_static.display = True
        for button in self.prompt_buttons:
            if button.label == BtnLabel.close:
                button.display = True
            if button.label in (BtnLabel.cancel, self.run_label):
                button.display = False

        cmd_enum = self.btn_label_to_cmd[self.btn_label]
        gen = tchezmoi.run_chezmoi_interactive(self.app, cmd_enum, self.path)

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
        finally:
            # on cancel/dismiss the worker is cancelled, this terminates chezmoi
            await gen.aclose()

    @on(Button.Pressed)
    def handle_prompt_btn_pressed(self, event: Button.Pressed) -> None:
        button_label = str(event.button.label)

        if button_label in (BtnLabel.cancel, BtnLabel.close):
            for worker in self.workers:
                worker.cancel()
            self.dismiss()
        elif button_label == self.run_label:
            self._run_interactive()
        elif self._prompt_future is not None and not self._prompt_future.done():
            for prompt in ChezmoiPrompts:
                if prompt.btn_label == button_label:
                    self._prompt_future.set_result(prompt.reply)
                    break


class LeftSideVertical(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        super().__init__(
            id=store.op_ids.container.left_side, classes=Tcss.operations_left
        )

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button(label=f"{store.cfg.dest_dir}", classes=Tcss.dest_dir_button),
            Button(label=Chars.refresh, classes=Tcss.refresh_button),
            classes=Tcss.tree_header,
        )
        yield OperateTree(
            TreeName.managed_only_sp,
            store.op_ids.tree.managed_only_sp,
        )
        yield OperateTree(
            TreeName.managed_only_sp_xpd,
            store.op_ids.tree.managed_only_sp_xpd,
        )
        yield OperateTree(
            TreeName.managed_all_mp,
            store.op_ids.tree.managed_all_mp,
        )
        yield OperateTree(
            TreeName.managed_all_mp_xpd,
            store.op_ids.tree.managed_all_mp_xpd,
        )
        # UNMANAGED TREE VARIANTS
        yield OperateTree(
            TreeName.un_man_plus_sp,
            store.op_ids.tree.un_man_plus_sp,
        )
        yield OperateTree(
            TreeName.un_man_plus_sp_xpd,
            store.op_ids.tree.un_man_plus_sp_xpd,
        )
        yield OperateTree(
            TreeName.un_man_plus_amp,
            store.op_ids.tree.un_man_plus_amp,
        )
        yield OperateTree(
            TreeName.un_man_plus_amp_xpd,
            store.op_ids.tree.un_man_plus_amp_xpd,
        )
        # UNWANTED TREE VARIANTS
        yield OperateTree(
            TreeName.un_wanted_plus_sp,
            store.op_ids.tree.un_wanted_plus_sp,
        )
        yield OperateTree(
            TreeName.un_wanted_plus_sp_xpd,
            store.op_ids.tree.un_wanted_plus_sp_xpd,
        )
        yield OperateTree(
            TreeName.un_wanted_plus_amp,
            store.op_ids.tree.un_wanted_plus_amp,
        )
        yield OperateTree(
            TreeName.un_wanted_plus_amp_xpd,
            store.op_ids.tree.un_wanted_plus_amp_xpd,
        )

    @property
    def current_displayed_tree(self) -> OperateTree:
        for tree in self.query_children(OperateTree).results():
            if tree.display is True:
                return tree
        raise RuntimeError("Expected a tree to be displayed.")

    @property
    def _non_displayed_trees(self) -> list[OperateTree]:
        return [
            tree
            for tree in self.query_children(OperateTree).results()
            if tree.display is False
        ]

    def sync_selected_node(self, path: Path) -> None:
        non_displayed_trees = [
            t for t in self.query_children(OperateTree).results() if t.display is False
        ]
        for tree in non_displayed_trees:
            tree_node = tree.node_map.get(path)
            if tree_node:
                tree.select_node(tree_node)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == Chars.refresh:
            event.stop()
            self._refresh_trees()

    def _update_trees(self) -> None:
        if store.cm_changes is None:
            return
        for tree in self.query(OperateTree).results():
            tree.apply_changes(store.cm_changes)

    @work
    async def _refresh_trees(self) -> None:
        await tchezmoi.run_managed_commands(self.app)
        if store.cm_changes is not None and not store.cm_changes.changes_available:
            self.notify("No changes available, skipping refresh.", severity="warning")
        else:
            self._update_trees()


class RightSideVertical(Vertical):
    def __init__(
        self,
        *,
        radio_labels: tuple[LabelStr, ...],
    ) -> None:
        self.radio_labels = radio_labels
        super().__init__(
            id=store.op_ids.container.right_side, classes=Tcss.operations_right
        )

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.context)
        with RadioSet():
            for radio_label in self.radio_labels:
                yield RadioButton(radio_label, compact=True)
        yield SwitchGroup()

    def on_mount(self) -> None:
        first_radio = self.query_exactly_one(RadioSet).query(RadioButton).first()
        if first_radio:
            first_radio.value = True


class PathView(Vertical): ...


class OperateTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        self.ids = store.op_ids
        super().__init__(
            id=BtnLabel.operate.pane_id,
            title=BtnLabel.operate,
        )

    def compose(self) -> ComposeResult:
        with Horizontal(classes=Tcss.operate_pane):
            yield LeftSideVertical()
            with Vertical(id=self.ids.container.middle, classes=Tcss.operations_middle):
                yield MainSectionLabel(LabelStr.dest_dir)
                yield GitLogView()
                yield ContentView()
                yield DiffView()
                yield DiffReverseView()
                with PathView():
                    yield FlatSectionLabel(LabelStr.select_path_git_log)
                    yield SubSectionLabel(str(store.cm_paths.dest_dir_node_data.path))
                    yield PathInfo()
            yield RightSideVertical(
                radio_labels=(
                    LabelStr.radio_git_log,
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                ),
            )
            yield OperateBtnGroup(
                store.op_ids,
                labels=(
                    BtnLabel.chezmoi_add,
                    BtnLabel.chezmoi_apply,
                    BtnLabel.chezmoi_re_add,
                    BtnLabel.chezmoi_forget,
                    BtnLabel.chezmoi_destroy,
                ),
            )

    def on_mount(self) -> None:
        # we can do this here as we await on mount in the splash screen
        self.left_side_vertical = self.query_exactly_one(LeftSideVertical)

        self.middle_section_label = self.query_one(
            self.ids.container.middle_q, Vertical
        ).query_exactly_one(MainSectionLabel)

        self.git_log_view = self.query_exactly_one(GitLogView)
        self.content_view = self.query_exactly_one(ContentView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)

        self.path_view = self.query_exactly_one(PathView)
        self.path_info = self.path_view.query_exactly_one(PathInfo)
        self.path_view_path = self.path_view.query_exactly_one(SubSectionLabel)
        self.no_show_label = self.path_view.query_exactly_one(FlatSectionLabel)

        self.op_buttons = (
            self.query_exactly_one(OperateBtnGroup).query(Button).results()
        )
        self._update_btn_states(store.cm_paths.dest_dir_node_data)

        self.radio_set = self.query_exactly_one(RadioSet)

        self.current_path = store.cm_paths.dest_dir_node_data.path

    @property
    def radio_to_view(
        self,
    ) -> dict[str, ContentView | DiffView | DiffReverseView | GitLogView]:
        return {
            LabelStr.radio_git_log: self.git_log_view,
            LabelStr.radio_contents: self.content_view,
            LabelStr.radio_diff: self.diff_view,
            LabelStr.radio_diff_reverse: self.diff_reverse_view,
        }

    @property
    def _current_radio_label(
        self,
    ) -> str:
        current_radio_btn = self.radio_set.pressed_button
        assert current_radio_btn is not None
        return str(current_radio_btn.label)

    @property
    def _current_radio_view(
        self,
    ) -> ContentView | DiffView | DiffReverseView | GitLogView:
        assert self.radio_set.pressed_button is not None
        return self.radio_to_view[str(self.radio_set.pressed_button.label)]

    def _update_no_show_label(self, radio_label: str) -> None:
        self.path_view_path.update(str(self.current_path))
        if radio_label == LabelStr.radio_git_log:
            self.no_show_label.update(LabelStr.select_path_git_log)
        elif radio_label == LabelStr.radio_contents:
            self.no_show_label.update(LabelStr.select_path_contents)
        elif radio_label in (LabelStr.radio_diff, LabelStr.radio_diff_reverse):
            self.no_show_label.update(LabelStr.select_path_diff)

    def _update_btn_states(self, node_data: NodeData) -> None:
        for btn in self.op_buttons:
            btn.disabled = not node_data.enable_op_btn_map[BtnLabel(str(btn.label))]

    def _update_all_widgets(self, node_data: NodeData) -> None:
        self.current_path = node_data.path
        self.middle_section_label.update(node_data.main_label)
        self._update_no_show_label(str(self.radio_set.pressed_button))
        self._update_btn_states(node_data)
        self.middle_section_label.update(node_data.main_label)
        self.path_info.node_data = node_data
        self.path_view.display = False

        if self._current_radio_label == LabelStr.radio_git_log:
            if node_data.path in self.git_log_view.view_data.displayed_paths:
                self.git_log_view.node_data = node_data
                self.git_log_view.display = True
            else:
                self.git_log_view.display = False
                self.path_view.display = True

        elif self._current_radio_label == LabelStr.radio_diff:
            if node_data.has_status:
                self.diff_view.node_data = node_data
                self.diff_view.display = True
            else:
                self.diff_view.display = False
                self.path_view.display = True

        elif self._current_radio_label == LabelStr.radio_diff_reverse:
            if node_data.has_status:
                self.diff_reverse_view.node_data = node_data
                self.diff_reverse_view.display = True
            else:
                self.diff_reverse_view.display = False
                self.path_view.display = True

        elif self._current_radio_label == LabelStr.radio_contents:
            if node_data.dir_path or node_data.path.is_dir():
                self.content_view.display = False
                self.path_info.display = True
            else:
                self.content_view.node_data = node_data
                self.content_view.display = True

    #################################
    # Watchers and message handling #
    #################################

    @on(ShowTreeQidMsg)
    def handle_show_tree(self, msg: ShowTreeQidMsg) -> None:
        # hide the current tree:
        all_trees = self.query(OperateTree).results()
        for tree in all_trees:
            tree.display = False
        show_tree = self.query_one(msg.tree_id_q, OperateTree)
        show_tree.display = True

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[NodeData]) -> None:
        event.stop()
        if (
            event.node.data is None
            or event.control.id != self.left_side_vertical.current_displayed_tree.id
        ):
            return
        self.left_side_vertical.sync_selected_node(event.node.data.path)
        self._update_all_widgets(event.node.data)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == str(store.cfg.dest_dir):
            event.stop()
            self._update_all_widgets(store.cm_paths.dest_dir_node_data)

    @on(Button.Pressed)
    def handle_operate_button(self, event: Button.Pressed) -> None:
        if event.button.label in (
            BtnLabel.chezmoi_add,
            BtnLabel.chezmoi_apply,
            BtnLabel.chezmoi_re_add,
            BtnLabel.chezmoi_forget,
            BtnLabel.chezmoi_destroy,
        ):
            event.stop()
            self.app.push_screen(
                ChezmoiCmdModal(str(event.button.label), self.current_path)
            )

    @on(RadioSet.Changed)
    def toggle_view(self, event: RadioSet.Changed) -> None:
        event.stop()
        target_view = self.radio_to_view[str(event.pressed.label)]
        self.notify(f"target view is {target_view}", severity="error")
