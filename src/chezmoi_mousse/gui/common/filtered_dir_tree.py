from collections.abc import Iterable
from pathlib import Path

from textual.reactive import reactive
from textual.widgets import DirectoryTree

from chezmoi_mousse import CMD, Chars

__all__ = ["FilteredDirTree"]

unwanted_dirs: set[str] = {
    "bin"
    "CMakeFiles"
    "Crash Reports"
    "DerivedData"
    "Desktop"
    "Documents"
    ".build"
    ".bundle"
    ".dart_tool"
    ".DS_Store"
    ".env"
    ".git"
    ".ipynb_checkpoints"
    ".mozilla"
    ".Trash"
    ".venv"
    "Downloads"
    "extensions"
    "go-build"
    "Music"
    "node_modules"
    "Pictures"
    "Public"
    "Recent"
    "temp"
    "Temp"
    "Templates"
    "tmp"
    "trash"
    "Trash"
    "Videos"
}

key_file_names: set[str] = {
    # As we don't support adding encrypted files yet, we are excluding them.
    # Common private key file names across platforms
    "id_rsa"
    "id_dsa"
    "id_ecdsa"
    "id_ed25519"
    "id_ecdsa_sk"  # FIDO/U2F ECDSA
    "id_ed25519_sk"  # FIDO/U2F Ed25519
    "identity"  # Legacy RSA1
    # Age encryption tool
    "age-key.txt"
    "keys.txt"  # common age key file name
    # Generic private key naming conventions
    "private_key"
    "privatekey"
    "priv_key"
    "privkey"
    # Terraform / cloud provider credentials
    "terraform.tfvars"  # often contains secrets
    "credentials"  # AWS credentials file pattern
    # Kubernetes
    "kubeconfig"
    # Wireguard
    "wg0.conf"  # contains PrivateKey
    "privatekey"
}

key_file_extensions: set[str] = {
    # Common private key file extensions
    # PuTTY private key files
    ".ppk"
    # GPG / PGP private key exports
    ".gpg"
    ".pgp"
    ".asc"
    # SSL/TLS private keys
    ".key"
    ".p12"
    ".pfx"
    # Generic private key naming conventions
    ".pem"
}

unwanted_suffixes: set[str] = {
    ".AppImage"
    ".bak"
    ".bin"
    ".coverage"
    ".doc"
    ".docx"
    ".egg-info"
    ".exe"
    ".gif"
    ".gz"
    ".img"
    ".iso"
    ".jar"
    ".jpeg"
    ".jpg"
    ".kdbx"
    ".lock"
    ".pdf"
    ".pid"
    ".png"
    ".ppk"
    ".ppt"
    ".pptx"
    ".rar"
    ".swp"
    ".tar"
    ".temp"
    ".tgz"
    ".tmp"
    ".7z"
    ".xls"
    ".xlsx"
    ".zip"
}


class FilteredDirTree(DirectoryTree):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    only_show_managed_dirs: reactive[bool] = reactive(False, init=False)
    show_unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.border_title = " destDir tree "

    def _could_be_private_key(self, file_path: Path) -> bool:
        return (
            file_path.suffix in key_file_extensions
            or file_path.parts[-1] in key_file_names
        )

    def _looks_like_cache(self, path: Path) -> bool:
        path_parts_lower = [p.lower() for p in path.parts]
        return any(
            p.startswith("cache") or p.endswith("cache") for p in path_parts_lower
        )

    def _looks_like_binary_file(self, file_path: Path) -> bool:
        try:
            if file_path.stat().st_size > 1024 * 1024:  # 1 MiB
                return True
            # Now read only first KiB
            with Path.open(file_path, "rb") as f:
                chunk = f.read(1024)
            return b"\x00" in chunk
        except OSError:
            return True

    def _is_unwanted_file(self, file_path: Path) -> bool:
        # always consider unwanted, regardless of the show_unwanted switch state
        if (
            self._could_be_private_key(file_path)
            or file_path in CMD.cache.sets.managed_files
        ):
            return True
        # always show the file otherwise
        elif self.show_unwanted:
            return False

        # logic with show_unwanted switch disabled
        return (
            file_path.parts[-1] in key_file_names
            or file_path.suffix in unwanted_suffixes
            or self._looks_like_cache(file_path)
            or self._looks_like_binary_file(file_path)
            or self._could_be_private_key(file_path)
        )

    # TODO fix filtering, add unmanaged cmd and add switch to unhide already managed

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        def is_unwanted_dir(dir_path: Path) -> bool:
            if (
                self.only_show_managed_dirs
                and dir_path not in {CMD.cache.dest_dir} | CMD.cache.sets.managed_dirs
            ):
                return True
            if self.show_unwanted:
                return False
            if not self.show_unwanted and dir_path.name in unwanted_dirs:
                return True

            def _has_unmanaged_paths_in(dir_path: Path) -> bool:
                try:
                    for p in dir_path.iterdir():
                        if p.is_file():
                            if (
                                p not in CMD.cache.sets.managed_files
                                and not self._could_be_private_key(p)
                            ):
                                return True
                        elif _has_unmanaged_paths_in(p) and p.name not in unwanted_dirs:
                            return True
                except (PermissionError, OSError):
                    return True
                return False

            if not _has_unmanaged_paths_in(dir_path):
                return True
            if self.show_unwanted:
                return False
            return False

        return (
            p
            for p in paths
            if (p.is_dir(follow_symlinks=False) and not is_unwanted_dir(p))
            or (p.is_file(follow_symlinks=False) and not self._is_unwanted_file(p))
        )
