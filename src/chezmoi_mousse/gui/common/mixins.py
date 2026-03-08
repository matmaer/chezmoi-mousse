from typing import TYPE_CHECKING

from chezmoi_mousse import CMD

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ContainerCache"]


class ContainerCache:

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
