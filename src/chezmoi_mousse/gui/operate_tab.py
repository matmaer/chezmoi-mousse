from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from rich.markup import escape
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
    PathView,
)
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Chars,
    ChezmoiPrompts,
    LabelStr,
    ReadCmd,
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
        dry_cmd = self.btn_label_to_dry_cmd[self.btn_label]
        flat_section_label.update(escape(f"{dry_cmd.pretty_cmd} {self.path}"))
        # run the command
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
            prompt.prompt_item
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
                if prompt.prompt_item == button_label:
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

    @on(Button.Pressed)
    def handle_refresh_tree_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == Chars.refresh:
            event.stop()
            self._refresh_trees()

    @work
    async def _refresh_trees(self) -> None:
        await tchezmoi.run_managed_commands(self.app)
        assert store.cm_changes is not None
        if not store.cm_changes.changes_available:
            self.notify("No changes available, skipping refresh.", severity="warning")
        else:
            for tree in self.query(OperateTree).results():
                tree.apply_changes(store.cm_changes)


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
                yield SubSectionLabel(escape(str(store.cfg.dest_dir)))
                yield GitLogView()
                yield ContentView()
                yield DiffView()
                yield DiffReverseView()
                yield PathView()
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
        self.left_side_vertical = self.query_exactly_one(LeftSideVertical)
        self.radio_set = self.query_exactly_one(RadioSet)
        self.path_label = self.query_exactly_one(SubSectionLabel)

        self.paths_without_git_log: set[Path] = set()
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.content_view = self.query_exactly_one(ContentView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)

        self.path_view = self.query_exactly_one(PathView)

        self._update_all_widgets(store.cm_paths.dest_dir_node_data)

        self.current_node: NodeData = store.cm_paths.dest_dir_node_data
        self.status_tree_fallback: NodeData = store.cm_paths.dest_dir_node_data
        self.managed_tree_fallback: NodeData = store.cm_paths.dest_dir_node_data
        self.un_wanted_tree_fallback: NodeData = store.cm_paths.dest_dir_node_data

    @property
    def _active_radio_btn(
        self,
    ) -> str:
        current_radio_btn = self.radio_set.pressed_button
        assert current_radio_btn is not None
        return str(current_radio_btn.label)

    @work
    async def _update_all_widgets(self, node_data: NodeData) -> None:
        self.path_label.update(escape(str(node_data.path)))
        self.current_node = node_data
        if node_data.has_status or node_data.has_nested_status:
            self.status_tree_fallback = node_data
            self.managed_tree_fallback = node_data
            self.un_managed_tree_fallback = node_data
        elif node_data.managed or node_data.has_status or node_data.has_nested_status:
            self.managed_tree_fallback = node_data
            self.un_managed_tree_fallback = node_data
        elif not node_data.managed and not node_data.un_wanted:
            self.un_managed_tree_fallback = node_data
        # update operate buttons
        op_buttons = self.query_exactly_one(OperateBtnGroup).query(Button).results()
        for btn in op_buttons:
            btn.disabled = not node_data.enable_op_btn_map[BtnLabel(str(btn.label))]
        # update middle main section label
        middle_label = self.query_one(
            self.ids.container.middle_q, Vertical
        ).query_exactly_one(MainSectionLabel)
        middle_label.update(node_data.main_label)
        # hide all views
        for view in (
            self.git_log_view,
            self.content_view,
            self.diff_view,
            self.diff_reverse_view,
            self.path_view,
        ):
            view.display = False

        if self._active_radio_btn == LabelStr.radio_git_log:
            if node_data.path in self.git_log_view.cache:
                self.git_log_view.update_git_log_view(node_data, None)
                self.git_log_view.display = True
            elif node_data.path not in self.paths_without_git_log and (
                node_data.managed or node_data.dest_dir
            ):
                cr = await tchezmoi.run_chezmoi_cmd(
                    self.app, ReadCmd.git_log, verb_arg=node_data.source_path
                )
                if cr.returncode != 0:
                    self.paths_without_git_log.add(node_data.path)
                else:
                    self.git_log_view.update_git_log_view(node_data, cr.std_out)
                    self.git_log_view.display = True
        elif self._active_radio_btn == LabelStr.radio_diff and node_data.has_status:
            self.diff_view.node_data = node_data
            self.diff_view.display = True
        elif (
            self._active_radio_btn == LabelStr.radio_diff_reverse
            and node_data.has_status
        ):
            self.diff_reverse_view.node_data = node_data
            self.diff_reverse_view.display = True
        elif self._active_radio_btn == LabelStr.radio_contents and (
            node_data.file_path or node_data.path.is_file()
        ):
            self.content_view.node_data = node_data
            self.content_view.display = True

        if all(
            view.display == False
            for view in (
                self.git_log_view,
                self.diff_view,
                self.diff_reverse_view,
                self.content_view,
            )
        ):
            # Update and display PathView
            self.path_view.path_info.node_data = node_data
            if self._active_radio_btn == LabelStr.radio_git_log:
                self.path_view.flat_label.update(LabelStr.select_path_git_log)
            elif self._active_radio_btn == LabelStr.radio_contents:
                self.path_view.flat_label.update(LabelStr.select_path_contents)
            elif self._active_radio_btn in (
                LabelStr.radio_diff,
                LabelStr.radio_diff_reverse,
            ):
                self.path_view.flat_label.update(LabelStr.select_path_diff)
            self.path_view.display = True

        # update other trees in the background
        non_displayed_trees = [
            t
            for t in self.left_side_vertical.query_children(OperateTree).results()
            if t.display is False
        ]
        for tree in non_displayed_trees:
            tree_node = tree.node_map.get(node_data.path)
            if tree_node:
                tree.select_node(tree_node)

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[NodeData]) -> None:
        event.stop()
        if (
            event.node.data is None
            or event.control.id != self.left_side_vertical.current_displayed_tree.id
        ):
            return
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
                ChezmoiCmdModal(str(event.button.label), self.current_node.path)
            )

    @on(ShowTreeQidMsg)
    def handle_show_tree(self, msg: ShowTreeQidMsg) -> None:
        msg.stop()
        # hide the current tree:
        all_trees = self.left_side_vertical.query_children(OperateTree).results()
        for tree in all_trees:
            tree.display = False
        show_tree = self.left_side_vertical.query_one(msg.tree_id_q, OperateTree)
        show_tree.display = True

        # the selected node is in the tree now shown, no fallback needed
        show_tree_node = show_tree.node_map.get(self.current_node.path)
        if show_tree_node is not None:
            return

        # fallback logic

        if show_tree.name in (TreeName.managed_only_sp, TreeName.managed_only_sp_xpd):
            self._update_all_widgets(self.status_tree_fallback)
        elif show_tree.name in (TreeName.managed_all_mp, TreeName.managed_all_mp_xpd):
            self._update_all_widgets(self.managed_tree_fallback)
        elif show_tree.name in (
            TreeName.un_man_plus_amp,
            TreeName.un_man_plus_amp_xpd,
            TreeName.un_man_plus_amp,
            TreeName.un_man_plus_amp_xpd,
        ):
            self._update_all_widgets(self.un_managed_tree_fallback)

    @on(RadioSet.Changed)
    def switch_radio_view(self, event: RadioSet.Changed) -> None:
        event.stop()
        self._update_all_widgets(self.current_node)
