import os
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, DirectoryTree, Label, Static, Switch

from chezmoi_mousse import CMD, IDS, AppType, OpBtnEnum, OpBtnLabel, Tcss

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.filtered_dir_tree import FilteredDirTree

__all__ = ["AddTab"]


class AddTabContentsView(ContentsView):

    show_path: reactive["Path | None"] = reactive(None)

    def on_mount(self) -> None:
        self.show_path = CMD.cache.dest_dir

    def _create_add_dir_container(self, dir_path: Path) -> ScrollableContainer:
        widgets: list[Static | Label] = []
        if dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            widgets.append(
                Static("<- Click a path to see its contents.", classes=Tcss.added)
            )
        unmanaged_dirs: list[str] = []
        unmanaged_files: list[str] = []
        output_limit = 50
        limited_dirs = False
        limited_files = False

        for root, dirs, _ in os.walk(dir_path):
            root_path = Path(root)

            for name in dirs:
                path = root_path / name
                if path not in CMD.cache.managed_dir_paths:
                    unmanaged_dirs.append(str(path.relative_to(CMD.cache.dest_dir)))
                    if len(unmanaged_dirs) >= output_limit:
                        limited_dirs = True
                        break
            if limited_dirs:
                break

        for root, _, files in os.walk(dir_path):
            root_path = Path(root)
            for name in files:
                path = root_path / name
                if path not in CMD.cache.managed_file_paths:
                    unmanaged_files.append(str(path.relative_to(CMD.cache.dest_dir)))
                    if len(unmanaged_files) >= output_limit:
                        limited_files = True
                        break
            if limited_files:
                break

        unmanaged_dirs.sort()
        unmanaged_files.sort()

        if unmanaged_dirs:
            widgets.append(
                Label("Contains unmanaged directories", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_dirs), classes=Tcss.info))
            if limited_dirs:
                widgets.append(
                    Label(
                        f"Limited output to {output_limit} unmanaged directories",
                        classes=Tcss.limited_label,
                    )
                )
        if unmanaged_files:
            widgets.append(
                Label("Contains unmanaged files", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_files), classes=Tcss.info))
            if limited_files:
                widgets.append(
                    Label(
                        f"Limited output to {output_limit} unmanaged files",
                        classes=Tcss.limited_label,
                    )
                )

        if not unmanaged_dirs and not unmanaged_files:
            widgets.append(Static("No unmanaged paths in this directory."))
        return ScrollableContainer(*widgets)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        container = self.container_cache.get(show_path, None)
        new_container: ScrollableContainer | None = None
        if container is None:
            # Create container based on path type
            if show_path == CMD.cache.dest_dir or show_path.is_dir():
                new_container = self._create_add_dir_container(show_path)
            elif show_path.is_file():
                new_container = self._create_file_container(show_path)
        self.update_container_display(show_path, new_container)


class AddTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__()
        self.op_btn_dict = OpBtnEnum.op_btn_enum_dict(IDS.add)

    def compose(self) -> ComposeResult:
        yield Vertical(
            FilteredDirTree(CMD.cache.dest_dir),
            Button(label=OpBtnLabel.refresh_tree, classes=Tcss.refresh_button),
            id=IDS.add.container.left_side,
            classes=Tcss.tab_left_vertical,
        )
        with Vertical():
            yield AddTabContentsView(IDS.add)
            yield OperateButtons(IDS.add, btn_dict=self.op_btn_dict)
        yield SwitchSlider(IDS.add)

    def on_mount(self) -> None:
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.query_exactly_one(FilteredDirTree).path = CMD.cache.dest_dir
        self.contents_view = self.query_one(
            IDS.add.container.contents_q, AddTabContentsView
        )
        self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        self.add_review_btn = self.query_one(IDS.add.op_btn.add_review_q, Button)
        self.add_review_btn.disabled = True

    @on(DirectoryTree.FileSelected)
    @on(DirectoryTree.DirectorySelected)
    def update_contents_view(
        self, event: DirectoryTree.FileSelected | DirectoryTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is None:
            raise ValueError("event.node.data is None in update_contents_view")

        if self.add_review_btn.disabled is True:
            self.add_review_btn.disabled = False
        self.contents_view.show_path = event.node.data.path
        self.contents_view.border_title = f" {event.node.data.path.name} "
        # Set path_arg for the btn_enums in OperateMode
        for btn_enum in self.op_btn_dict.values():
            if isinstance(btn_enum, OpBtnEnum):
                btn_enum.path_arg = event.node.data.path

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.add.switch.unmanaged_dirs:
            self.dir_tree.unmanaged_dirs = event.value
        elif event.switch.id == IDS.add.switch.unwanted:
            self.dir_tree.unwanted = event.value
        self.dir_tree.reload()
