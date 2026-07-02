from itertools import groupby
from pathlib import Path

from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import (
    CMD,
    AppIds,
    ReadCmd,
    SectionLabel,
    StatusCode,
    TabLabel,
    Tcss,
)

from .actionables import DirContentBtn
from .messages import LogCmdResultMsg

__all__ = ["DiffView"]

DIFF_TCSS = {
    " ": Tcss.context,
    "@@": Tcss.context,
    "index": Tcss.context,
    "-": Tcss.removed,
    "deleted": Tcss.removed,
    "old": Tcss.removed,
    "+": Tcss.added,
    "new": Tcss.added,
    "changed": Tcss.changed,
    "unhandled": Tcss.unhandled,
}


class DiffView(Container):

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff)
        self.ids = ids

    def _create_diff_widgets(self, path: Path) -> list[Label | Static | DirContentBtn]:
        widgets: list[Label | Static | DirContentBtn] = []
        if self.ids.canvas_name == TabLabel.apply:
            diff_result = CMD.run_cmd.read(ReadCmd.diff, path_arg=path)
        else:  # re-add tab
            diff_result = CMD.run_cmd.read(ReadCmd.diff_reverse, path_arg=path)
        self.post_message(LogCmdResultMsg(diff_result))
        diff_lines = diff_result.std_out.splitlines()
        if not diff_lines:
            return [Static("No diff output available.", classes=Tcss.info)]
        diff_cmd = diff_lines.pop(0)
        widgets.append(Label(diff_cmd, classes=Tcss.flat_section_label))

        def get_prefix(line: str) -> str:
            for p in DIFF_TCSS:
                if line.startswith(p):
                    return p
            return "unhandled"

        for prefix, group_lines in groupby(diff_lines, key=get_prefix):
            group_list = list(group_lines)
            if prefix in ("+", "-"):
                text = "\n".join(group_list)
                widgets.append(
                    Static(text, classes=DIFF_TCSS[prefix].value, markup=False)
                )
            else:
                for line in group_list:
                    widgets.append(
                        Static(line, classes=DIFF_TCSS[prefix].value, markup=False)
                    )
        return widgets

    def _get_status_files(self, app_ids: AppIds) -> dict[Path, StatusCode]:
        if CMD.cache.cmd_results.status_files is None:
            return {}
        fs_pairs = {
            Path(line[3:]): line[:2]
            for line in CMD.cache.cmd_results.status_files.std_out.splitlines()
        }
        fs_idx = 0 if app_ids.canvas_name == TabLabel.apply else 1  # file status index
        return {
            k: StatusCode(v[fs_idx])
            for k, v in fs_pairs.items()
            if v[fs_idx] != StatusCode.Space
        }

    def _get_status_files_descendants(
        self, dir_path: Path, app_ids: AppIds
    ) -> dict[Path, StatusCode]:
        status_files = self._get_status_files(app_ids)
        results: dict[Path, StatusCode] = {}
        for path, status in status_files.items():
            if path.is_relative_to(dir_path):
                results[path] = status
        return results

    def _get_status_dirs(self, app_ids: AppIds) -> dict[Path, StatusCode]:
        if CMD.cache.cmd_results.status_dirs is None:
            return {}
        ds_pairs = {
            Path(line[3:]): line[:2]
            for line in CMD.cache.cmd_results.status_dirs.std_out.splitlines()
        }
        ds_idx = 0 if app_ids.canvas_name == TabLabel.apply else 1  # dir status index
        return {
            k: StatusCode(v[ds_idx])
            for k, v in ds_pairs.items()
            if v[ds_idx] != StatusCode.Space
        }

    def _get_status_dir_descendants(
        self, dir_path: Path, app_ids: AppIds
    ) -> dict[Path, StatusCode]:
        status_dirs = self._get_status_dirs(app_ids)
        results: dict[Path, StatusCode] = {}
        for path, status in status_dirs.items():
            if path.is_relative_to(dir_path):
                results[path] = status
        return results

    def _get_unchanged_file_paths_in(self, dir_path: Path) -> list[Path]:
        results: set[Path] = set()
        for path in CMD.cache.sets.x_files:
            if path.is_relative_to(dir_path):
                results.add(path)
        return sorted(results)

    def _get_unchanged_dir_paths_in(self, dir_path: Path) -> list[Path]:
        results: set[Path] = set()
        for path in CMD.cache.sets.x_dirs:
            if path != dir_path and path.is_relative_to(dir_path):
                results.add(path)
        return sorted(results)

    def _get_dir_widgets(
        self, dir_path: Path, app_ids: AppIds
    ) -> list[Static | Label | DirContentBtn]:
        widgets: list[Static | Label | DirContentBtn] = []
        if dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
        if CMD.cache.sets.no_managed_paths is True:
            widgets = [
                Label(SectionLabel.paths_with_status, classes=Tcss.main_section_label)
            ]
            widgets.append(
                Static(
                    "No managed paths are in the chezmoi repository, "
                    "switch to the Add tab to add some paths.",
                    classes=Tcss.added,
                )
            )
            return widgets
        elif CMD.cache.sets.no_status_paths is True:
            widgets.append(
                Label(SectionLabel.paths_with_status, classes=Tcss.main_section_label)
            )
            widgets.append(
                Static(
                    "No diffs are available because no paths have a status. Toggle "
                    "the 'Show unchanged paths' switch to view all managed paths.",
                    classes=Tcss.info,
                )
            )
            return widgets

        if CMD.cache.sets.contains_status_paths(dir_path):
            status_dirs_in = self._get_status_dir_descendants(dir_path, app_ids).items()
            if status_dirs_in:
                widgets.append(
                    Label(
                        "Contains directories with a status",
                        classes=Tcss.sub_section_label,
                    )
                )
                for path, status in status_dirs_in:
                    widgets.append(
                        DirContentBtn(label=f"{status.color_tag}{path}[/]", path=path)
                    )
            status_files_in = self._get_status_files_descendants(dir_path, app_ids)
            if status_files_in:
                widgets.append(
                    Label(
                        "Contains files with a status", classes=Tcss.sub_section_label
                    )
                )
                for path, status in status_files_in.items():
                    widgets.append(
                        DirContentBtn(label=f"{status.color_tag}{path}[/]", path=path)
                    )

        unchanged_dirs = self._get_unchanged_dir_paths_in(dir_path)
        if unchanged_dirs:
            widgets.append(
                Label("Contains unchanged directories", classes=Tcss.sub_section_label)
            )
            for path in unchanged_dirs:
                widgets.append(DirContentBtn(label=f"[dim]{path}[/]", path=path))

        unchanged_files = self._get_unchanged_file_paths_in(dir_path)
        if unchanged_files:
            widgets.append(
                Label("Contains unchanged files", classes=Tcss.sub_section_label)
            )
            for path in unchanged_files:
                widgets.append(DirContentBtn(label=f"[dim]{path}[/]", path=path))
        return widgets

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.remove_children()
        widgets: list[Label | Static | DirContentBtn] = []
        if show_path == CMD.cache.dest_dir:
            widgets = self._get_dir_widgets(show_path, self.ids)
        elif show_path in CMD.cache.sets.managed_dirs:
            if show_path in CMD.cache.sets.status_dirs:
                widgets = self._create_diff_widgets(show_path)
            else:
                widgets = self._get_dir_widgets(show_path, self.ids)
        elif show_path in CMD.cache.sets.managed_files:
            if show_path in CMD.cache.sets.status_files:
                widgets = self._create_diff_widgets(show_path)
            else:
                widgets.append(Label("Managed file", classes=Tcss.main_section_label))
                widgets.append(Label(str(show_path), classes=Tcss.sub_section_label))
                widgets.append(Static("This file has no status.", classes=Tcss.context))
        else:
            widgets.append(Static("Nothing to show."))
        container = ScrollableContainer(*widgets)
        self.mount(container)
