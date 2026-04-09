import os
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import DirectoryTree, Label, Static, Switch

from chezmoi_mousse import CMD, IDS, OpBtnEnum, Tcss, Utils

from .common.actionables import OpButton, OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.filtered_dir_tree import FilteredDirTree

__all__ = ["AddTab"]


OUTPUT_LIMIT = 40


class AddTabContentsView(ContentsView):

    show_path: reactive["Path | None"] = reactive(None)

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

        limited_dirs = False
        limited_files = False

        for root, dirs, _ in os.walk(dir_path):
            root_path = Path(root)

            for name in dirs:
                path = root_path / name
                if path not in CMD.cache.sets.managed_dirs:
                    unmanaged_dirs.append(str(path.relative_to(CMD.cache.dest_dir)))
                    if len(unmanaged_dirs) >= OUTPUT_LIMIT:
                        limited_dirs = True
                        break
            if limited_dirs:
                break

        for root, _, files in os.walk(dir_path):
            root_path = Path(root)
            for name in files:
                path = root_path / name
                if path not in CMD.cache.sets.managed_files:
                    unmanaged_files.append(str(path.relative_to(CMD.cache.dest_dir)))
                    if len(unmanaged_files) >= OUTPUT_LIMIT:
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
                        f"Limited output to {OUTPUT_LIMIT} unmanaged directories",
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
                        f"Limited output to {OUTPUT_LIMIT} unmanaged files",
                        classes=Tcss.limited_label,
                    )
                )

        if not unmanaged_dirs and not unmanaged_files:
            widgets.append(Static("No unmanaged paths in this directory."))
        return ScrollableContainer(*widgets)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.hide_all_containers()
        sc_id = Utils.path_to_id(show_path)
        sc_id_q = Utils.path_to_qid(show_path)
        try:
            container = self.query_one(sc_id_q, ScrollableContainer)
            container.display = True
        except NoMatches as e:
            if show_path == CMD.cache.dest_dir or show_path.is_dir():
                container = self._create_add_dir_container(show_path)
            elif show_path.is_file():
                container = self._create_file_container(show_path)
            else:
                raise ValueError(f"{show_path} does not exist") from e
            self.mount(container)
            self.mounted[show_path] = sc_id
        self.current_path = show_path


class AddTab(Horizontal):

    def compose(self) -> ComposeResult:
        yield Vertical(
            FilteredDirTree(CMD.cache.dest_dir),
            OpButton(
                btn_enum=OpBtnEnum.refresh_tree,
                btn_id=IDS.add.op_btn.refresh_tree,
                app_ids=IDS.add,
            ),
            id=IDS.add.container.left_side,
            classes=Tcss.tab_left_vertical,
        )
        with Vertical():
            yield AddTabContentsView(IDS.add)
            yield OperateButtons(IDS.add)
        yield SwitchSlider(IDS.add)

    def on_mount(self) -> None:
        refresh_btn = self.query_one(IDS.add.op_btn.refresh_tree_q, OpButton)
        refresh_btn.remove_class(Tcss.operate_button)
        refresh_btn.add_class(Tcss.refresh_button)
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.contents_view = self.query_one(
            IDS.add.container.contents_q, AddTabContentsView
        )
        self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        self.add_review_btn = self.query_one(IDS.add.op_btn.add_review_q, OpButton)

    @on(DirectoryTree.FileSelected)
    @on(DirectoryTree.DirectorySelected)
    def update_contents_view(
        self, event: DirectoryTree.FileSelected | DirectoryTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is None:
            raise ValueError("event.node.data is None in update_contents_view")
        if event.node.data.path == CMD.cache.dest_dir:
            self.dir_tree.root.expand()
        self.contents_view.show_path = event.node.data.path
        if event.node.data.path == CMD.cache.dest_dir:
            self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        else:
            self.contents_view.border_title = f" {event.node.data.path.name} "
        # Set path_arg for the btn_enums in OperateMode
        operate_buttons = self.query_one(
            IDS.add.container.operate_buttons_q, OperateButtons
        )
        operate_buttons.set_path_arg(event.node.data.path)
        if isinstance(event, DirectoryTree.DirectorySelected):
            self.add_review_btn.disabled = True
        else:  # isinstance(event, DirectoryTree.FileSelected):
            self.add_review_btn.disabled = False

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.add.switch.managed_dirs:
            self.dir_tree.only_show_managed_dirs = event.value
        elif event.switch.id == IDS.add.switch.unwanted:
            self.dir_tree.show_unwanted = event.value
        self.dir_tree.reload()
