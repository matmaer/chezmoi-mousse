from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import PathKind, SectionLabel, Tcss

from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["ContentsView"]


class ContentsView(Container):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.contents)

    def _create_dir_container(self, dir_path: Path) -> ScrollableContainer:
        widgets: list[Static | Label] = []
        if dir_path == self.app.cmattr.dest_dir:
            widgets.append(
                Label(SectionLabel.dest_dir, classes=Tcss.main_section_label)
            )
        elif dir_path in self.app.cmattr.paths.managed_dirs:
            widgets.append(
                Label(SectionLabel.managed_dir, classes=Tcss.main_section_label)
            )
        else:
            widgets.append(
                Label(SectionLabel.unmanaged_dir, classes=Tcss.main_section_label)
            )
        widgets.append(
            Static("<- Click a file path to see its contents.", classes=Tcss.info)
        )
        return ScrollableContainer(*widgets)

    def _create_file_container(self, file_path: Path) -> ScrollableContainer:
        widgets: list[Label | Static] = []
        if file_path in self.app.cmattr.paths.managed_files:
            widgets.append(
                Label(SectionLabel.managed_file, classes=Tcss.main_section_label)
            )
        else:
            widgets.append(
                Label(SectionLabel.unmanaged_file, classes=Tcss.main_section_label)
            )

        if self.app.cmattr.paths.managed_files.get(file_path) is PathKind.EXISTS_FALSE:
            widgets.append(
                Label(SectionLabel.chezmoi_cat_output, classes=Tcss.sub_section_label)
            )
            f_content, cmd_result = Commands.get_highlighted_chezmoi_cat_output(
                file_path
            )
            self.post_message(LogCmdResultMsg(cmd_result))
            widgets.append(Static(f_content))
        else:
            widgets.append(
                Label(SectionLabel.read_file_output, classes=Tcss.sub_section_label)
            )
            f_content = Commands.get_highlighted_file_contents(file_path)
            widgets.append(Static(f_content))

        return ScrollableContainer(*widgets)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.remove_children()
        if (
            show_path in (self.app.cmattr.dest_dir, self.app.cmattr.paths.managed_dirs)
            or show_path.is_dir()  # for the add tab
        ):
            container = self._create_dir_container(show_path)
        else:
            container = self._create_file_container(show_path)
        self.mount(container)
        self.current_path = show_path
