from typing import TYPE_CHECKING, ClassVar

from textual.containers import Container, ScrollableContainer
from textual.widget import Widget
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import AppType, ContainerName

if TYPE_CHECKING:
    from pathlib import Path


BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}

__all__ = ["ContainerCache"]


class ContainerCache(AppType, Container):

    LANGUAGE_MAP = BUILTIN_MAP | {
        ".cfg": BUILTIN_MAP["toml"],
        ".ini": BUILTIN_MAP["toml"],
        ".sh": BUILTIN_MAP["bash"],
        ".yml": BUILTIN_MAP["yaml"],
        ".zsh": BUILTIN_MAP["bash"],
    }
    SHEBANG_MAP: ClassVar = {
        "python": "python",
        "python3": "python",
        "bash": "bash",
        "sh": "bash",
        "zsh": "bash",
        "node": "javascript",
        "java": "java",
        "go": "go",
        "rustc": "rust",
    }

    def __init__(
        self, *children: Widget, id: str | None = None, container: ContainerName
    ) -> None:
        super().__init__(*children, id=id)
        self.container = container
        self.container_cache: dict[Path, ScrollableContainer] = {}
        self.current_container_path: Path | None = None

    def update_container_display(
        self, show_path: "Path", new_container: "ScrollableContainer | None"
    ) -> None:
        # Hide the previously displayed container
        previous_container: ScrollableContainer | None = None
        if self.current_container_path is not None:
            previous_container = self.container_cache.get(self.current_container_path)
        if previous_container is not None:
            previous_container.display = False
        if new_container is not None:
            # Cache the new container
            self.container_cache[show_path] = new_container
            self.mount(new_container)
        else:
            # Display the cached container
            self.container_cache[show_path].display = True
        # Update the current container path
        self.current_container_path = show_path

    def purge_mounted_containers(self) -> None:
        for cached_path in list(self.container_cache.keys()):
            container = self.container_cache.pop(cached_path, None)
            if container is not None:
                container.remove()
