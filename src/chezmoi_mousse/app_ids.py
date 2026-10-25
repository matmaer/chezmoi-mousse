from __future__ import annotations

from typing import TYPE_CHECKING

from chezmoi_mousse.str_enums import ContainerName, LabelStr, RichLogName, TreeName

if TYPE_CHECKING:
    from chezmoi_mousse.str_enums import BtnLabel

__all__ = ["AppIds"]


class AppIds:
    def __init__(self, tab_label: BtnLabel) -> None:
        self.tab_label = tab_label
        self.container = _ContainerIds(self)
        self.richlog = _RichLogIds(self)
        self.switch = _SwitchIds(self)
        self.tree = _TreeIds(self)

    def container_id(self, qid: str = "", *, name: ContainerName) -> str:
        return f"{qid}{self.tab_label.name}_{name.name}_id"

    def switch_id(self, qid: str = "", *, switch_label: LabelStr) -> str:
        return f"{qid}{self.tab_label.name}_{switch_label.name}_switch_id"

    def richlog_id(self, qid: str = "", *, richlog: RichLogName) -> str:
        return f"{qid}{self.tab_label.name}_{richlog.name}_id"

    def tree_id(self, qid: str = "", *, tree_name: TreeName) -> str:
        return f"{qid}{self.tab_label.name}_{tree_name.name}_tree_id"


class _ContainerIds:
    def __init__(self, ids: AppIds) -> None:
        self.cat_config: str = ids.container_id(name=ContainerName.cat_config)
        self.cmd_log: str = ids.container_id(name=ContainerName.cmd_log)
        self.color_vars: str = ids.container_id(name=ContainerName.color_vars)
        self.debug_log: str = ids.container_id(name=ContainerName.debug_log)
        self.diagram: str = ids.container_id(name=ContainerName.diagram)
        self.doctor: str = ids.container_id(name=ContainerName.doctor)
        self.dom_nodes: str = ids.container_id(name=ContainerName.dom_nodes)
        self.dump_config: str = ids.container_id(name=ContainerName.dump_config)
        self.flat_buttons: str = ids.container_id(name=ContainerName.flat_buttons)
        self.flat_buttons_q: str = f"#{self.flat_buttons}"
        self.ignored: str = ids.container_id(name=ContainerName.git_ignored)
        self.env_vars: str = ids.container_id(name=ContainerName.env_vars)
        self.operate_buttons: str = ids.container_id(name=ContainerName.operate_buttons)
        self.operate_buttons_q: str = f"#{self.operate_buttons}"
        self.prompt_buttons: str = ids.container_id(name=ContainerName.prompt_buttons)
        self.template_data: str = ids.container_id(name=ContainerName.template_data)
        self.test_paths_view: str = ids.container_id(name=ContainerName.test_paths_view)
        self.test_paths_view_q: str = f"#{self.test_paths_view}"


class _RichLogIds:
    def __init__(self, ids: AppIds) -> None:
        self.app: str = ids.richlog_id(richlog=RichLogName.app_logger)
        self.debug: str = ids.richlog_id(richlog=RichLogName.debug_logger)
        self.dom_nodes: str = ids.richlog_id(richlog=RichLogName.dom_node_logger)
        self.dom_nodes_q: str = f"#{self.dom_nodes}"
        self.env_vars: str = ids.richlog_id(richlog=RichLogName.env_var_logger)
        self.env_vars_q: str = f"#{self.env_vars}"
        self.memory: str = ids.richlog_id(richlog=RichLogName.memory_usage_logger)


class _SwitchIds:
    def __init__(self, ids: AppIds) -> None:

        self.expand_managed: str = ids.switch_id(switch_label=LabelStr.expand_managed)
        self.expand_managed_q: str = f"#{self.expand_managed}"

        self.show_unchanged: str = ids.switch_id(switch_label=LabelStr.show_unchanged)
        self.show_unchanged_q: str = f"#{self.show_unchanged}"

        self.show_unmanaged: str = ids.switch_id(switch_label=LabelStr.show_unmanaged)
        self.show_unmanaged_q: str = f"#{self.show_unmanaged}"

        self.show_unwanted: str = ids.switch_id(switch_label=LabelStr.show_unwanted)
        self.show_unwanted_q: str = f"#{self.show_unwanted}"


class _TreeIds:
    def __init__(self, ids: AppIds) -> None:

        # status trees never include managed without status
        self.managed_sp: str = ids.tree_id(tree_name=TreeName.managed_sp)
        self.managed_sp_q: str = f"#{self.managed_sp}"
        self.managed_sp_xpd: str = ids.tree_id(tree_name=TreeName.managed_sp_xpd)
        self.managed_sp_xpd_q: str = f"#{self.managed_sp_xpd}"

        # managed trees always with unchanged
        self.managed_amp: str = ids.tree_id(tree_name=TreeName.managed_amp)
        self.managed_amp_q: str = f"#{self.managed_amp}"
        self.managed_amp_xpd: str = ids.tree_id(tree_name=TreeName.managed_amp_xpd)
        self.managed_amp_xpd_q: str = f"#{self.managed_amp_xpd}"

        # 1 --- UN_MANAGED TREE ---

        # 1.1 WANTED UN MANAGED TREE PLUS TREE STATUS PATHS

        # 1.1.1 NON XPD
        self.wanted_plus_sp: str = ids.tree_id(tree_name=TreeName.wanted_plus_sp)
        self.wanted_plus_sp_q: str = f"#{self.wanted_plus_sp}"

        # 1.1.2 XPD
        self.wanted_plus_sp_xpd: str = ids.tree_id(
            tree_name=TreeName.wanted_plus_sp_xpd
        )
        self.wanted_plus_sp_xpd_q: str = f"#{self.wanted_plus_sp_xpd}"

        # 1.2 UN_MANAGED TREE PLUS ALL MANAGED PATHS

        # 1.2.1 NON XPD
        self.wanted_plus_amp: str = ids.tree_id(tree_name=TreeName.wanted_plus_amp)
        self.wanted_plus_amp_q: str = f"#{self.wanted_plus_amp}"

        # 1.2.2 XPD
        self.wanted_plus_amp_xpd: str = ids.tree_id(
            tree_name=TreeName.wanted_plus_amp_xpd
        )
        self.wanted_plus_amp_xpd_q: str = f"#{self.wanted_plus_amp_xpd}"

        # 2 --- UN_WANTED TREE ---

        # 2.1 UN_WANTED TREE PLUS TREE STATUS PATHS

        # 2.1.1 NON XPD
        self.un_wanted_plus_sp: str = ids.tree_id(tree_name=TreeName.un_wanted_plus_sp)
        self.un_wanted_plus_sp_q: str = f"#{self.un_wanted_plus_sp}"

        # 2.1.2 XPD
        self.un_wanted_plus_sp_xpd: str = ids.tree_id(
            tree_name=TreeName.un_wanted_plus_sp_xpd
        )
        self.un_wanted_plus_sp_xpd_q: str = f"#{self.un_wanted_plus_sp_xpd}"

        # 2.2 UN_WANTED TREE PLUS ALL MANAGED PATHS

        # 2.2.1 NON XPD
        self.un_wanted_plus_amp: str = ids.tree_id(
            tree_name=TreeName.un_wanted_plus_amp
        )
        self.un_wanted_plus_amp_q: str = f"#{self.un_wanted_plus_amp}"

        # 2.2.2 XPD
        self.un_wanted_plus_amp_xpd: str = ids.tree_id(
            tree_name=TreeName.un_wanted_plus_amp_xpd
        )
        self.un_wanted_plus_amp_xpd_q: str = f"#{self.un_wanted_plus_amp_xpd}"
