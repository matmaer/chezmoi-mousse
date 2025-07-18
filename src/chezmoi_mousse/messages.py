from textual.message import Message

from chezmoi_mousse.chezmoi import OperateData


class OperateMessage(Message):
    def __init__(self, dismiss_data: OperateData) -> None:
        self.dismiss_data: OperateData = dismiss_data
        super().__init__()
