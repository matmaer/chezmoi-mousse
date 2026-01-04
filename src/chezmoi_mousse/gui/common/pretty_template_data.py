import json

from textual.widgets import Pretty

from chezmoi_mousse import CommandResult

__all__ = ["PrettyTemplateData"]


class PrettyTemplateData(Pretty):
    def __init__(self, template_data: CommandResult) -> None:
        parsed = json.loads(template_data.std_out)
        super().__init__(parsed)
