from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

from textual.reactive import reactive
from textual.widgets import DirectoryTree

from chezmoi_mousse import CMD, Chars

__all__ = ["FilteredDirTree"]


class FilteredDirTree(DirectoryTree):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    only_show_managed_dirs: reactive[bool] = reactive(False, init=False)
    show_unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.border_title = " destDir tree "

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:

        def is_unwanted_file(file_path: Path) -> bool:
            if (
                KeyFileNames.is_unwanted(file_path)
                or file_path in CMD.cache.sets.managed_files
            ):
                return True
            if file_path not in CMD.cache.sets.managed_files:
                try:
                    if file_path.stat().st_size > 1024 * 1024:  # 1 MiB
                        return True
                    # Now read only first KiB
                    with Path.open(file_path, "rb") as f:
                        chunk = f.read(1024)
                    return b"\x00" in chunk
                except OSError:
                    return True
            if not self.show_unwanted and UnwantedFileExtensions.is_unwanted(file_path):
                return True
            if self.show_unwanted:
                return False
            return False

        def is_unwanted_dir(dir_path: Path) -> bool:
            if (
                self.only_show_managed_dirs
                and dir_path not in {CMD.cache.dest_dir} | CMD.cache.sets.managed_dirs
            ):
                return True
            if not self.show_unwanted and UnwantedDirs.is_unwanted(dir_path.name):
                return True

            def _has_unmanaged_paths_in(dir_path: Path) -> bool:
                try:
                    for p in dir_path.iterdir():
                        if p.is_file():
                            if (
                                p not in CMD.cache.sets.managed_files
                                and not KeyFileNames.is_unwanted(p)
                            ):
                                return True
                        elif _has_unmanaged_paths_in(
                            p
                        ) and not UnwantedDirs.is_unwanted(p.name):
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
            or (p.is_file(follow_symlinks=False) and not is_unwanted_file(p))
        )


class UnwantedDirs(StrEnum):
    bin = "bin"
    CMakeFiles = "CMakeFiles"
    Crash_Reports = "Crash Reports"
    DerivedData = "DerivedData"
    Desktop = "Desktop"
    Documents = "Documents"
    dot_build = ".build"
    dot_bundle = ".bundle"
    dot_dart_tool = ".dart_tool"
    dot_ds_store = ".DS_Store"
    dot_env = ".env"
    dot_git = ".git"
    dot_ipynb_checkpoints = ".ipynb_checkpoints"
    dot_mozilla = ".mozilla"
    dot_trash = ".Trash"
    dot_venv = ".venv"
    Downloads = "Downloads"
    extensions = "extensions"
    go_build = "go-build"
    Music = "Music"
    node_modules = "node_modules"
    Pictures = "Pictures"
    Public = "Public"
    Recent = "Recent"
    temp = "temp"
    Temp = "Temp"
    Templates = "Templates"
    tmp = "tmp"
    trash = "trash"
    Trash = "Trash"
    Videos = "Videos"

    @classmethod
    def is_unwanted(cls, name: str) -> bool:
        try:
            cls(name)
            return True
        except ValueError:
            return "cache" in name.lower()


class UnwantedFileExtensions(StrEnum):
    AppImage = ".AppImage"
    bak = ".bak"
    bin = ".bin"
    coverage = ".coverage"
    doc = ".doc"
    docx = ".docx"
    egg_info = ".egg-info"
    exe = ".exe"
    gif = ".gif"
    gz = ".gz"
    img = ".img"
    iso = ".iso"
    jar = ".jar"
    jpeg = ".jpeg"
    jpg = ".jpg"
    kdbx = ".kdbx"
    lock = ".lock"
    pdf = ".pdf"
    pid = ".pid"
    png = ".png"
    ppk = ".ppk"
    ppt = ".ppt"
    pptx = ".pptx"
    rar = ".rar"
    swp = ".swp"
    tar = ".tar"
    temp = ".temp"
    tgz = ".tgz"
    tmp = ".tmp"
    seven_zip = ".7z"
    xls = ".xls"
    xlsx = ".xlsx"
    zip = ".zip"

    @classmethod
    def is_unwanted(cls, file_path: Path) -> bool:
        if KeyFileNames.is_unwanted(file_path):
            return True
        try:
            cls(file_path.suffix)
            return True
        except ValueError:
            if file_path.parent.name == ".ssh" and file_path.name != "config":
                return True
            return "cache" in file_path.name.lower()


class KeyFileNames(StrEnum):
    """As we don't support adding encrypted files yet, we are excluding them."""

    # Common private key files across platforms (generated by ssh-keygen)
    id_rsa = "id_rsa"
    id_dsa = "id_dsa"
    id_ecdsa = "id_ecdsa"
    id_ed25519 = "id_ed25519"
    id_ecdsa_sk = "id_ecdsa_sk"  # FIDO/U2F ECDSA
    id_ed25519_sk = "id_ed25519_sk"  # FIDO/U2F Ed25519
    identity = "identity"  # Legacy RSA1
    # PuTTY private key files
    id_rsa_ppk = "id_rsa.ppk"
    id_dsa_ppk = "id_dsa.ppk"
    id_ecdsa_ppk = "id_ecdsa.ppk"
    id_ed25519_ppk = "id_ed25519.ppk"
    # GPG / PGP private key exports
    secring_gpg = "secring.gpg"
    private_key_asc = "private-key.asc"
    private_key_pgp = "private-key.pgp"
    secret_key_asc = "secret-key.asc"
    # SSL/TLS private keys
    server_key = "server.key"
    client_key = "client.key"
    private_key_pem = "private.key"
    private_key_p12 = "private.p12"
    private_key_pfx = "private.pfx"
    # Age encryption tool
    age_key_txt = "age-key.txt"
    keys_txt = "keys.txt"  # common age key file name
    # Generic private key naming conventions
    private_key = "private_key"
    privatekey = "privatekey"
    priv_key = "priv_key"
    privkey = "privkey"
    privkey_pem = "privkey.pem"
    key_pem = "key.pem"
    # Terraform / cloud provider credentials
    terraform_tfvars = "terraform.tfvars"  # often contains secrets
    credentials = "credentials"  # AWS credentials file pattern
    # Kubernetes
    kubeconfig = "kubeconfig"
    # Wireguard
    wg0_conf = "wg0.conf"  # contains PrivateKey
    privatekey_wg = "privatekey"

    @classmethod
    def is_unwanted(cls, file_path: Path) -> bool:
        try:
            cls(file_path.name)
            return True
        except ValueError:
            if file_path.parent.name == ".ssh" and file_path.name != "config":
                return True
            return "cache" in file_path.name.lower()
