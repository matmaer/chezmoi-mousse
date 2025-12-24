"""Contains subclassed textual classes shared across the application."""

from ._actionables import (
    FlatButton,
    FlatButtonsVertical,
    FlatLink,
    LogsTabButtons,
    OperateButtons,
    SwitchWithLabel,
    TreeTabButtons,
    ViewTabButtons,
)
from ._config_views import (
    DoctorTable,
    DoctorTableView,
    PrettyTemplateData,
    TemplateDataView,
)
from ._custom_collapsible import CustomCollapsible
from ._git_log_view import GitLogGlobal, GitLogPath
from ._loggers import AppLog, DebugLog, OperateLog, ReadCmdLog
from ._messages import (
    CurrentAddNodeMsg,
    CurrentApplyNodeMsg,
    CurrentReAddDiffMsg,
    CurrentReAddNodeMsg,
    InitCloneCmdMsg,
    OperateButtonMsg,
)
from ._pw_mgr_info import PwMgrInfoView
from ._screen_header import CustomHeader, HeaderTitle

__all__ = [
    # Buttons, Links and Switches
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "LogsTabButtons",
    "OperateButtons",
    "SwitchWithLabel",
    "TreeTabButtons",
    "ViewTabButtons",
    # Loggers
    "AppLog",
    "DebugLog",
    "OperateLog",
    "ReadCmdLog",
    # Messages
    "CurrentAddNodeMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddDiffMsg",
    "CurrentReAddNodeMsg",
    "InitCloneCmdMsg",
    "OperateButtonMsg",
    # Other shared components
    "CustomCollapsible",
    "CustomHeader",
    "DoctorTable",
    "DoctorTableView",
    "GitLogGlobal",
    "GitLogPath",
    "HeaderTitle",
    "PrettyTemplateData",
    "PwMgrInfoView",
    "TemplateDataView",
]
