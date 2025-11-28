"""Contains subclassed textual classes shared across the application."""

from ._buttons import (
    FlatButton,
    FlatButtonsVertical,
    FlatLink,
    LogsTabButtons,
    OperateButtons,
    TreeTabButtons,
    ViewTabButtons,
)
from ._config_views import (
    CatConfigView,
    DoctorTableView,
    IgnoredView,
    TemplateDataView,
)
from ._contents_view import ContentsView
from ._custom_collapsible import CustomCollapsible
from ._dest_dir_info import DestDirInfo
from ._diff_view import DiffView
from ._git_log_view import GitLogGlobal, GitLogPath
from ._loggers import AppLog, DebugLog, OperateLog, ReadCmdLog
from ._operate_msg import (
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
)
from ._pw_mgr_info import PwMgrInfoView
from ._screen_header import CustomHeader
from ._section_headers import (
    FlatSectionLabel,
    MainSectionLabel,
    SubSectionLabel,
)

__all__ = [
    # Loggers
    "AppLog",
    "DebugLog",
    "OperateLog",
    "ReadCmdLog",
    # Messages
    "CurrentAddNodeMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    # Buttons
    "FlatButton",
    "FlatButtonsVertical",
    "LogsTabButtons",
    "OperateButtons",
    "TreeTabButtons",
    "ViewTabButtons",
    # Other shared components
    "CatConfigView",
    "ContentsView",
    "CustomCollapsible",
    "CustomHeader",
    "DestDirInfo",
    "DiffView",
    "DoctorTableView",
    "FlatLink",
    "FlatSectionLabel",
    "GitLogGlobal",
    "GitLogPath",
    "IgnoredView",
    "MainSectionLabel",
    "PwMgrInfoView",
    "SubSectionLabel",
    "TemplateDataView",
]
