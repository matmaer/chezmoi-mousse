from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import tchezmoi
from chezmoi_mousse.str_enums import BtnLabel

if TYPE_CHECKING:
    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


type BtnDryDataDict = dict[BtnLabel, str | None]
type BtnDryCompletedDict = dict[BtnLabel, str]
type PathDryDict = dict[Path, dict[BtnLabel, str]]


__all__ = ["BtnDryDataDict", "CachedCommands"]


@dataclass(slots=True)
class _BtnDryResults:
    _node_data: NodeData
    chezmoi_add: str | None = None
    chezmoi_apply: str | None = None
    chezmoi_destroy: str | None = None
    chezmoi_forget: str | None = None
    chezmoi_re_add: str | None = None

    def __post_init__(self) -> None:
        if self._node_data.dir_data.dest_dir:
            self._dest_dir_defaults()
            return
        if self._node_data.managed:
            self._managed_defaults()
        if not self._node_data.managed:
            self._unmanaged_defaults()
        if not self._node_data.exists:
            self._exists_defaults()

    @property
    def _field_map(self) -> dict[str, str | None]:
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if not f.name.startswith("_")
        }

    @property
    def has_none_fields(self) -> bool:
        return bool([f for f, v in self._field_map.items() if v is None])

    @property
    def btn_dict(self) -> BtnDryDataDict:
        field_map = self._field_map
        return {
            btn_label: field_map[btn_label.name]
            for btn_label in BtnLabel.op_btn_labels()
        }

    @property
    def complete_btn_dict(self) -> BtnDryCompletedDict:
        field_map = self._field_map
        complete_dict: BtnDryCompletedDict = {}
        for btn_label in BtnLabel.op_btn_labels():
            result = field_map[btn_label.name]
            if result is None:
                raise RuntimeError(f"Missing dry result for {btn_label.name}")
            complete_dict[btn_label] = result
        return complete_dict

    def _dest_dir_defaults(self) -> None:
        self.chezmoi_add = ""
        self.chezmoi_forget = ""
        self.chezmoi_destroy = ""
        if not self._node_data.dir_data.nested_status:
            self.chezmoi_apply = ""
            self.chezmoi_re_add = ""
        return

    def _unmanaged_defaults(self) -> None:
        for cmd_field in fields(self):
            if cmd_field.name != "chezmoi_add":
                setattr(self, cmd_field.name, "")

    def _managed_defaults(self) -> None:
        if self._node_data.file_path and self._node_data.status is None:
            self.chezmoi_apply = ""
            self.chezmoi_re_add = ""

    def _exists_defaults(self) -> None:
        self.chezmoi_destroy = ""
        self.chezmoi_add = ""


@dataclass(slots=True)
class CachedCommands:
    _app: ChezmoiGui
    path_dry_dict: PathDryDict = field(default_factory=dict[Path, dict[BtnLabel, str]])

    async def get_dry_results(self, node_data: NodeData) -> dict[BtnLabel, str]:
        current = self.path_dry_dict.get(node_data.path, None)
        if current is not None:
            return current
        defaults = _BtnDryResults(node_data)
        if not defaults.has_none_fields:
            complete_results = defaults.complete_btn_dict
            self.path_dry_dict[node_data.path] = complete_results
            return complete_results

        btn_results = defaults.btn_dict
        new_result = await tchezmoi.collect_chezmoi_paths_in_scope(
            self._app, node_data.path, btn_results
        )
        complete_results: BtnDryCompletedDict = {}
        for btn_label, result in btn_results.items():
            if result is None:
                complete_results[btn_label] = new_result[btn_label]
            else:
                complete_results[btn_label] = result

        self.path_dry_dict[node_data.path] = complete_results
        return complete_results
