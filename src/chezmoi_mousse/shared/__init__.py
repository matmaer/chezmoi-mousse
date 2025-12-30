"""Contains subclassed textual classes shared across the application."""

from ._actionables import (
    CloseButton,
    FlatButton,
    FlatButtonsVertical,
    FlatLink,
    LogsTabButtons,
    OpButton,
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
from ._loggers import AppLog, DebugLog, OperateLog, ReadCmdLog
from ._messages import (
    CloseButtonMsg,
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
    InitCloneCmdMsg,
    OperateButtonMsg,
)
from ._operate_info import OperateInfo
from ._pw_mgr_info import PwMgrInfoView
from ._screen_header import CustomHeader, HeaderTitle

__all__ = [
    # Buttons, Links and Switches
    "CloseButton",
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "LogsTabButtons",
    "OpButton",
    "OperateButtons",
    "OperateInfo",
    "SwitchWithLabel",
    "TreeTabButtons",
    "ViewTabButtons",
    # Loggers
    "AppLog",
    "DebugLog",
    "OperateLog",
    "ReadCmdLog",
    # Messages
    "CloseButtonMsg",
    "CurrentApplyNodeMsg",
    "CurrentReAddNodeMsg",
    "InitCloneCmdMsg",
    "OperateButtonMsg",
    # Other shared components
    "CustomCollapsible",
    "CustomHeader",
    "DoctorTable",
    "DoctorTableView",
    "HeaderTitle",
    "PrettyTemplateData",
    "PwMgrInfoView",
    "TemplateDataView",
]
