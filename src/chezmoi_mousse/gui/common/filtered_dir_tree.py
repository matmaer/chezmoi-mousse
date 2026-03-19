from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

from textual.reactive import reactive
from textual.widgets import DirectoryTree

from chezmoi_mousse import CMD, AppType, BorderTitle, Chars

__all__ = ["FilteredDirTree"]


class FilteredDirTree(DirectoryTree, AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded
    ICON_FILE = " "

    unmanaged_dirs: reactive[bool] = reactive(False, init=False)
    unwanted: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.guide_depth = 3
        self.show_root = False
        self.border_title = BorderTitle.dest_dir

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        show_unmanaged = bool(self.unmanaged_dirs)
        show_unwanted = bool(self.unwanted)

        def is_unwanted_file(fp: Path) -> bool:
            return UnwantedFileNames.is_unwanted(
                fp
            ) or UnwantedFileExtensions.is_unwanted(fp)

        def dir_matches(d: Path) -> bool:
            if show_unwanted and UnwantedDirs.is_unwanted(d.name):
                return True
            if (
                show_unmanaged
                and self._has_unmanaged_paths_in(d)
                and not UnwantedDirs.is_unwanted(d.name)
            ):
                return True
            return d in CMD.cache.sets.managed_dirs_plus_dest_dir

        def file_matches(f: Path) -> bool:
            if is_unwanted_file(f):
                return show_unwanted
            if not self._file_of_interest(f):
                return False
            if show_unmanaged:
                parent_ok = (
                    f.parent in CMD.cache.sets.managed_dirs_plus_dest_dir
                    or self._has_unmanaged_paths_in(f.parent)
                )
                return f not in CMD.cache.sets.managed_files and parent_ok
            return f in CMD.cache.sets.managed_files

        return (
            p
            for p in paths
            if (p.is_dir() and dir_matches(p)) or (p.is_file() and file_matches(p))
        )

    def _file_of_interest(self, file_path: Path) -> bool:
        if UnwantedFileNames.is_unwanted(
            file_path
        ) or UnwantedFileExtensions.is_unwanted(file_path):
            return False
        try:
            if file_path.stat().st_size > 1000 * 1024:  # 1 MiB
                return False
            # Now read only first 8 KiB
            with Path.open(file_path, "rb") as f:
                chunk = f.read(8192)
            return b"\x00" not in chunk
        except OSError:
            return False

    def _has_unmanaged_paths_in(self, dir_path: Path) -> bool:
        try:
            for p in dir_path.iterdir():
                if p.is_file():
                    if (
                        p not in CMD.cache.sets.managed_files
                        and self._file_of_interest(p)
                    ):
                        return True
                elif (
                    p.is_dir(follow_symlinks=False)
                    and self._has_unmanaged_paths_in(p)
                    and not UnwantedDirs.is_unwanted(p.name)
                ):
                    return True
            return False
        except (PermissionError, OSError):
            return False


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
        if UnwantedFileNames.is_unwanted(file_path):
            return True
        try:
            cls(file_path.suffix)
            return True
        except ValueError:
            if file_path.parent.name == ".ssh" and file_path.name != "config":
                return True
            return "cache" in file_path.name.lower()


class UnwantedFileNames(StrEnum):
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
