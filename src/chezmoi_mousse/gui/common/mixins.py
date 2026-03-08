from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.widget import Widget
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import CMD, AppType

if TYPE_CHECKING:
    from pathlib import Path


BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}

__all__ = ["ContainerCache"]


class ContainerCache(AppType, Container):

    def __init__(self, *children: Widget, id: str | None = None) -> None:
        super().__init__(*children, id=id)
        self.container_cache: dict[Path, ScrollableContainer] = {}
        self.current_container_path: Path | None = None
        self.language_map = BUILTIN_MAP | {
            ".cfg": BUILTIN_MAP["toml"],
            ".ini": BUILTIN_MAP["toml"],
            ".sh": BUILTIN_MAP["bash"],
            ".yml": BUILTIN_MAP["yaml"],
            ".zsh": BUILTIN_MAP["bash"],
        }
        self.shebang_map = {
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

    def purge_mounted_containers(self, changed_paths: list["Path"]) -> None:
        # Remove exact changed paths and anything cached under those paths
        keys_to_remove: list[Path] = [
            cached_path
            for cached_path in self.container_cache
            if any(
                cached_path == changed_path or changed_path in cached_path.parents
                for changed_path in changed_paths
            )
        ]

        for cached_path in keys_to_remove:
            container = self.container_cache.pop(cached_path, None)
            if container is not None:
                container.remove()

        if self.current_container_path in keys_to_remove:
            self.current_container_path = None

        self.show_path = CMD.cache.dest_dir
