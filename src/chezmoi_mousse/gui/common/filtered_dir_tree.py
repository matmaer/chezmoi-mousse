import os
from collections.abc import Iterable
from pathlib import Path

from textual.reactive import reactive
from textual.widgets import DirectoryTree

from chezmoi_mousse import CMD, Chars

__all__ = ["FilteredDirTree"]

GIT_OBJECT_DIR: str = f"{os.sep}{Path(".git", "objects")}{os.sep}"

UNWANTED_DIRS: set[str] = {
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
    "bin"
    "CMakeFiles"
    "Crash Reports"
    "DerivedData"
    "Desktop"
    "Documents"
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

KEY_FILE_NAMES: set[str] = {
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

KEY_FILE_EXTENSIONS: set[str] = {
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

UNWANTED_FILE_SUFFIXES: set[str] = {
    ".7z"
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
    ".xls"
    ".xlsx"
    ".zip"
}

# lightweight functions only needing a file or dir path, regardless of filter settings,
# only returning a bool


class CheckPath:

    @staticmethod
    def looks_like_cache(path: Path) -> bool:
        path_parts_lower = [p.lower() for p in path.parts]
        return any(
            p.startswith("cache") or p.endswith("cache") for p in path_parts_lower
        )


class CheckFile:

    @staticmethod
    def is_sensitive(file_path: Path) -> bool:
        return (
            file_path.suffix in KEY_FILE_EXTENSIONS
            or file_path.parts[-1] in KEY_FILE_NAMES
        )

    @staticmethod
    def is_large(file_path: Path) -> bool:
        # check if it's a large file, typically not a dot file
        return file_path.stat().st_size > 1024 * 1024  # 1 MiB

    @staticmethod
    def is_binary(file_path: Path) -> bool:
        # check if the file looks like a binary
        try:
            with Path.open(file_path, "rb") as f:
                chunk = f.read(1024)  # Read only first KiB
            return b"\x00" in chunk  # typically the case for binary files
        except OSError:
            return True

    @staticmethod
    def is_bad_suffix(file_path: Path) -> bool:
        return file_path.suffix in UNWANTED_FILE_SUFFIXES


class CheckDir:

    @staticmethod
    def has_unwanted_name(dir_path: Path) -> bool:
        return dir_path.parts[-1] in UNWANTED_DIRS

    @staticmethod
    def has_many_children(dir_path: Path, max_entries: int = 200) -> bool:
        # TODO: make this configurable but 200 entries seems like a reasonable limit
        # for a directory to consider interesting in the context of dotfiles.
        with os.scandir(dir_path) as entries:
            count = 0
            for _ in entries:
                try:
                    count += 1
                    if count > max_entries:
                        return True
                except Exception:
                    continue
            return False


class FilteredDirTree(DirectoryTree):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    hide_unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    show_managed: reactive[bool] = reactive(False, init=False)
    show_unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.border_title = " destDir tree "

    def _is_unwanted_file(self, file_path: Path) -> bool:
        return (
            CheckFile.is_bad_suffix(file_path)
            or CheckFile.is_large(file_path)
            or CheckFile.is_binary(file_path)
        )

    def _is_unwanted_dir(self, dir_path: Path) -> bool:
        return CheckDir.has_unwanted_name(dir_path) or CheckDir.has_many_children(
            dir_path
        )

    def _has_wanted_unmanaged_files(self, dir_path: Path) -> bool:
        return bool(
            {
                p
                for p in CMD.cache.sets.all_unmanaged_files_in(dir_path)
                if not self._is_unwanted_file(p)
            }
        )

    def _has_wanted_unmanaged_dirs(self, dir_path: Path) -> bool:
        return bool(
            {
                p
                for p in CMD.cache.sets.all_unmanaged_dirs_in(dir_path)
                if not self._is_unwanted_dir(p)
            }
        )

    def _show_file(self, file_path: Path) -> bool:

        if CheckFile.is_sensitive(file_path):
            return False

        if file_path in CMD.cache.sets.managed_files:
            return self.hide_unmanaged_dirs

        if (
            file_path.parent not in CMD.cache.sets.managed_dirs
            and self.hide_unmanaged_dirs is True
        ):
            return False

        return self._is_unwanted_file(file_path)

    def _show_dir(self, dir_path: Path) -> bool:

        if dir_path not in CMD.cache.sets.managed_dirs:
            return not self.hide_unmanaged_dirs

        return True

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        return (
            p
            for p in paths
            if (self.show_unwanted and CheckPath.looks_like_cache(p))
            or (p.is_dir(follow_symlinks=False) and self._show_dir(p))
            or (p.is_file(follow_symlinks=False) and self._show_file(p))
        )
