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
    ReactiveVar,
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
            yield SubSectionLabel(LabelStr.not_set)
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
        # set sub section label with the command to run
        sub_section_label = self.query_exactly_one(SubSectionLabel)
        pretty_run_cmd = (
            f"{self.btn_label_to_cmd[self.btn_label].pretty_cmd} {self.path}"
        )
        sub_section_label.update(f"Dry run: {pretty_run_cmd}")
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
    def _current_displayed_tree(self) -> OperateTree:
        for tree in self.query_children(OperateTree).results():
            if tree.display is True:
                return tree
        return self.query_one(store.op_ids.tree.managed_only_sp_q, OperateTree)

    @property
    def _non_displayed_trees(self) -> list[OperateTree]:
        return [
            tree
            for tree in self.query_children(OperateTree).results()
            if tree.display is False
        ]

    def _sync_to_trees(self, node_data: NodeData, exclude: list[OperateTree]) -> None:
        for tree in self._non_displayed_trees:
            if tree in exclude:
                continue
            tree_node = tree.node_map.get(node_data.path)
            if tree_node:
                tree.select_node(tree_node)

    @on(Tree.NodeSelected)
    def sync_selected_node(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            return
        if (
            self._current_displayed_tree.id is None
            or event.control.id != self._current_displayed_tree.id
            or (
                event.control.id
                in (
                    store.op_ids.tree.un_wanted_plus_sp,
                    store.op_ids.tree.un_wanted_plus_amp,
                )
                and event.node.data.status == None
            )
        ):
            return
        exclude: list[OperateTree] = []
        if event.node.data.status in (None, None):
            exclude.extend(
                [
                    self.query_one(store.op_ids.tree.managed_only_sp_q, OperateTree),
                    self.query_one(
                        store.op_ids.tree.managed_only_sp_xpd_q, OperateTree
                    ),
                ]
            )
        if event.node.data.status in (None, None):
            exclude.extend(
                [
                    self.query_one(store.op_ids.tree.managed_all_mp_q, OperateTree),
                    self.query_one(store.op_ids.tree.managed_all_mp_xpd_q, OperateTree),
                ]
            )
        if event.node.data.status is None:
            exclude.extend(
                [
                    self.query_one(store.op_ids.tree.un_man_plus_sp_q, OperateTree),
                    self.query_one(store.op_ids.tree.un_man_plus_amp_q, OperateTree),
                    self.query_one(store.op_ids.tree.un_man_plus_sp_xpd_q, OperateTree),
                    self.query_one(
                        store.op_ids.tree.un_man_plus_amp_xpd_q, OperateTree
                    ),
                ]
            )
        self._sync_to_trees(event.node.data, exclude=exclude)

    @on(Tree.NodeCollapsed)
    def sync_collapsed_node(self, event: Tree.NodeCollapsed[NodeData]) -> None: ...

    @on(Tree.NodeExpanded)
    def sync_expanded_node(self, event: Tree.NodeExpanded[NodeData]) -> None: ...

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == Chars.refresh:
            event.stop()
            self.refresh_trees()

    def _update_trees(self) -> None:
        if store.cm_changes is None:
            return
        for tree in self.query(OperateTree).results():
            tree.apply_changes(store.cm_changes)

    @work
    async def refresh_trees(self) -> None:
        self._current_displayed_tree.loading = True
        await tchezmoi.run_managed_commands(self.app)
        if store.cm_changes is not None and not store.cm_changes.changes_available:
            self.notify("No changes available, skipping refresh.", severity="warning")
        else:
            self._update_trees()
        self._current_displayed_tree.loading = False


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
        middle_vertical = self.query_one(self.ids.container.middle_q, Vertical)
        self.middle_section_label = middle_vertical.query_exactly_one(MainSectionLabel)
        self.middle_section_label.update(LabelStr.dest_dir)
        self.op_btn_group = self.query_exactly_one(OperateBtnGroup)
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.content_view = self.query_exactly_one(ContentView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self._set_all_path_reactives(store.cm_paths.dest_dir_node_data)

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

    def _set_all_path_reactives(self, node_data: NodeData) -> None:
        self.current_path = node_data.path
        setattr(self.git_log_view, ReactiveVar.node_data, node_data)
        setattr(self.content_view, ReactiveVar.node_data, node_data)
        setattr(self.diff_view, ReactiveVar.node_data, node_data)
        setattr(self.diff_reverse_view, ReactiveVar.node_data, node_data)

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            return
        event.stop()
        self.middle_section_label.update(event.node.data.main_label)
        self._set_all_path_reactives(event.node.data)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == str(store.cfg.dest_dir):
            event.stop()
            self.middle_section_label.update(LabelStr.dest_dir)
            self._set_all_path_reactives(store.cm_paths.dest_dir_node_data)
            for btn in self.op_btn_group.query(Button).results():
                if btn.label == BtnLabel.chezmoi_destroy:
                    btn.disabled = True
                if btn.label == BtnLabel.chezmoi_forget:
                    btn.disabled = True

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
        if event.pressed.label == LabelStr.radio_git_log:
            self.git_log_view.display = True
            self.content_view.display = False
            self.diff_view.display = False
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_contents:
            self.git_log_view.display = False
            self.content_view.display = True
            self.diff_view.display = False
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_diff:
            self.git_log_view.display = False
            self.content_view.display = False
            self.diff_view.display = True
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_diff_reverse:
            self.git_log_view.display = False
            self.content_view.display = False
            self.diff_view.display = False
            self.diff_reverse_view.display = True
