from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import tchezmoi
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


type DryDefaultsDict = dict[BtnLabel, str | None]
type PathDryDict = dict[Path, dict[BtnLabel, str]]


__all__ = ["CachedCommands", "DryDefaultsDict"]


@dataclass(slots=True)
class _DryDefaults:
    _node_data: NodeData
    chezmoi_add: str | None = None
    chezmoi_apply: str | None = None
    chezmoi_destroy: str | None = None
    chezmoi_forget: str | None = None
    chezmoi_re_add: str | None = None

    def __post_init__(self) -> None:
        if self._node_data.dir_data.dest_dir:
            self._dest_dir_defaults()
        elif self._node_data.managed:
            if self._node_data.file_path:
                self._managed_file_defaults()
            else:
                self._managed_dir_defaults()
        else:
            self._unmanaged_defaults()

    @property
    def btn_dict(self) -> DryDefaultsDict:
        return {label: getattr(self, label.name) for label in BtnLabel.op_btn_labels()}

    @property
    def is_complete(self) -> bool:
        return None not in (
            self.chezmoi_add,
            self.chezmoi_apply,
            self.chezmoi_destroy,
            self.chezmoi_forget,
            self.chezmoi_re_add,
        )

    def _dest_dir_defaults(self) -> None:
        self.chezmoi_add = ""
        self.chezmoi_forget = ""
        self.chezmoi_destroy = ""
        if self._node_data.dir_data.nested_status is False:
            self.chezmoi_apply = ""
            self.chezmoi_re_add = ""
        return

    def _unmanaged_defaults(self) -> None:
        self.chezmoi_apply = ""
        self.chezmoi_destroy = ""
        self.chezmoi_forget = ""
        self.chezmoi_re_add = ""

    def _managed_file_defaults(self) -> None:
        if self._node_data.status is None:
            self.chezmoi_apply = ""
            self.chezmoi_re_add = ""
        self._exists_defaults()

    def _managed_dir_defaults(self) -> None:
        dir_data = self._node_data.dir_data
        if self._node_data.status is None and not dir_data.nested_status:
            self.chezmoi_apply = ""
            self.chezmoi_re_add = ""
        if (
            self._node_data.status is None
            and not dir_data.nested_status
            and not dir_data.nested_un_managed
        ):
            self.chezmoi_add = ""
        self._exists_defaults()

    def _exists_defaults(self) -> None:
        if not self._node_data.exists:
            self.chezmoi_add = ""
            self.chezmoi_destroy = ""
            self.chezmoi_re_add = ""


from chezmoi_mousse import store


@dataclass(slots=True)
class CachedCommands:
    _app: ChezmoiGui
    _complete_dicts: dict[Path, dict[BtnLabel, str]] = field(
        default_factory=dict[Path, dict[BtnLabel, str]]
    )
    _dry_defaults: dict[Path, _DryDefaults] = field(
        default_factory=dict[Path, _DryDefaults]
    )

    def __post_init__(self) -> None:
        self._dry_defaults = {}
        for path, node_data in store.cm_paths.all_node_data.items():
            self._dry_defaults[path] = _DryDefaults(node_data)

    async def get_dry_results(self, node_data: NodeData) -> dict[BtnLabel, str]:
        if node_data.path in self._complete_dicts:
            return self._complete_dicts[node_data.path]

        defaults = self._dry_defaults[node_data.path]
        if defaults.is_complete:
            complete = {k: v for k, v in defaults.btn_dict.items() if v is not None}
            self._complete_dicts[node_data.path] = complete
            return complete
        new_result = await tchezmoi.collect_chezmoi_paths_in_scope(
            self._app, node_data.path, self._dry_defaults[node_data.path].btn_dict
        )
        self._complete_dicts[node_data.path] = new_result
        return new_result
