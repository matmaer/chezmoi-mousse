from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer

from chezmoi_mousse import CMD, AppType

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ContainerCache"]


class ContainerCache(AppType, Container):

    def update_container_display(
        self, show_path: "Path", new_container: "ScrollableContainer | None"
    ) -> None:
        # Hide the previously displayed container
        previous_container = self.container_cache.get(  # type: ignore[attr-defined]
            self.current_container_path, None
        )
        if previous_container is not None:
            previous_container.display = False
        if new_container is not None:
            # Cache the new container
            self.container_cache[show_path] = new_container  # type: ignore[attr-defined]
            self.mount(new_container)
        else:
            # Display the cached container
            self.container_cache[show_path].display = True  # type: ignore[attr-defined]
        # Update the current container path
        self.current_container_path = show_path  # type: ignore[attr-defined]

    def purge_mounted_containers(self, changed_paths: list["Path"]) -> None:
        # Remove exact changed paths and anything cached under those paths
        keys_to_remove: list[Path] = [
            cached_path
            for cached_path in self.container_cache  # type: ignore[attr-defined]
            if any(
                cached_path == changed_path or changed_path in cached_path.parents  # type: ignore[attr-defined]
                for changed_path in changed_paths
            )
        ]

        for cached_path in keys_to_remove:
            container = self.container_cache.pop(cached_path, None)  # type: ignore[attr-defined]
            if container is not None:
                container.remove()  # type: ignore[attr-defined]

        if self.current_container_path in keys_to_remove:  # type: ignore[attr-defined]
            self.current_container_path = None  # type: ignore[attr-defined]

        self.show_path = CMD.cache.dest_dir  # type: ignore[attr-defined]
