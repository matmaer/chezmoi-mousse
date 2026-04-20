from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Switch, TabPane

from chezmoi_mousse import CMD, AppIds, OpBtnEnum, TabLabel, Tcss

from .common.actionables import OpButton, OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.filtered_dir_tree import FilteredDirTree

__all__ = ["AddTab"]


class AddTab(TabPane):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=TabLabel.add, title=TabLabel.add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Vertical(
                FilteredDirTree(CMD.cache.dest_dir),
                OpButton(
                    btn_enum=OpBtnEnum.refresh_tree,
                    btn_id=self.ids.op_btn.refresh_tree,
                    app_ids=self.ids,
                ),
                id=self.ids.container.left_side,
                classes=Tcss.tab_left_vertical,
            )
            with Vertical():
                yield ContentsView(self.ids)
                yield OperateButtons(self.ids)
        yield SwitchSlider(self.ids)

    def on_mount(self) -> None:
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.contents_view = self.query_one(self.ids.container.contents_q, ContentsView)
        self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        self.contents_view.show_path = CMD.cache.dest_dir
        self.add_review_btn = self.query_one(self.ids.op_btn.add_review_q, OpButton)

    @on(DirectoryTree.FileSelected)
    @on(DirectoryTree.DirectorySelected)
    def update_contents_view(
        self, event: DirectoryTree.FileSelected | DirectoryTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is None:
            raise ValueError("event.node.data is None in update_contents_view")
        self.contents_view.show_path = event.node.data.path
        if event.node.data.path == CMD.cache.dest_dir:
            self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        else:
            self.contents_view.border_title = f" {event.node.data.path.name} "
        # Set path_arg for the btn_enums in OperateMode
        operate_buttons = self.query_one(
            self.ids.container.operate_buttons_q, OperateButtons
        )
        operate_buttons.set_path_arg(event.node.data.path)
        if isinstance(event, DirectoryTree.DirectorySelected):
            self.add_review_btn.disabled = True
        else:  # isinstance(event, DirectoryTree.FileSelected):
            self.add_review_btn.disabled = False

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch.managed_dirs:
            self.dir_tree.only_show_managed_dirs = event.value
        elif event.switch.id == self.ids.switch.unwanted:
            self.dir_tree.show_unwanted = event.value
        self.dir_tree.reload()
