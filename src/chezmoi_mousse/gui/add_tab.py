from collections.abc import Callable, Iterable
from enum import StrEnum
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, DirectoryTree, Switch

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    BorderTitle,
    Chars,
    FlatBtnLabel,
    OpBtnEnum,
    OpBtnLabel,
    Tcss,
)

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.operate_mode import OperateMode

__all__ = ["AddTab"]


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
        # Define condition lambdas for each switch combo
        conditions: dict[tuple[bool, bool], Callable[[Path], bool]] = {
            (False, False): lambda p: (  # switches: Red - Red (default)
                (
                    p.is_dir()
                    and not UnwantedDirs.is_unwanted(p.name)
                    and p in CMD.cache.managed_dir_paths
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file()
                    and not UnwantedFileExtensions.is_unwanted(p.suffix)
                    and not UnwantedFileNames.is_unwanted(p.name)
                    and p.parent in CMD.cache.managed_dir_paths
                    and p not in CMD.cache.managed_file_paths
                    and self._file_of_interest(p)
                    and not UnwantedFileNames.is_private_key_name(p.name)
                )
            ),
            (True, False): lambda p: (  # switches: Green - Red
                (
                    p.is_dir()
                    and not UnwantedDirs.is_unwanted(p.name)
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file()
                    and not UnwantedFileExtensions.is_unwanted(p.suffix)
                    and not UnwantedFileNames.is_unwanted(p.name)
                    and (
                        p.parent in CMD.cache.managed_dir_paths
                        or self._has_unmanaged_paths_in(p.parent)
                    )
                    and p not in CMD.cache.managed_file_paths
                    and self._file_of_interest(p)
                    and not UnwantedFileNames.is_private_key_name(p.name)
                )
            ),
            (False, True): lambda p: (  # switches: Red - Green
                (
                    p.is_dir()
                    and p in CMD.cache.managed_dir_paths
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file()
                    and p not in CMD.cache.managed_file_paths
                    and p.parent in CMD.cache.managed_dir_paths
                    and not UnwantedFileNames.is_private_key_name(p.name)
                )
            ),
            # switches: Green - Green, include all unmanaged paths
            (True, True): lambda p: (
                (p.is_dir() and self._has_unmanaged_paths_in(p))
                or (
                    p.is_file()
                    and p not in CMD.cache.managed_file_paths
                    and not UnwantedFileNames.is_private_key_name(p.name)
                )
            ),
        }

        # Select the condition based on switches and filter
        key = (self.unmanaged_dirs, self.unwanted)
        return (p for p in paths if conditions[key](p))

    def _file_of_interest(self, file_path: Path) -> bool:
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
        # Assume a directory with more than max_entries is not of interest
        max_entries = 300
        try:
            # Special case for .ssh: only show if config is unmanaged
            if dir_path.name == ".ssh":
                config_path = dir_path / "config"
                return (
                    config_path.exists()
                    and config_path not in CMD.cache.managed_file_paths
                )
            for idx, p in enumerate(dir_path.iterdir(), start=1):
                if idx > max_entries:
                    return False
                elif (
                    p not in CMD.cache.managed_dir_paths
                    and p not in CMD.cache.managed_file_paths
                ):
                    return True
            return False
        except (PermissionError, OSError):
            return False


class AddTab(Horizontal, AppType):

    def compose(self) -> ComposeResult:
        yield Vertical(
            FilteredDirTree(CMD.cache.dest_dir),
            Button(label=FlatBtnLabel.refresh_tree, classes=Tcss.refresh_button),
            id=IDS.add.container.left_side,
            classes=Tcss.tab_left_vertical,
        )
        with Vertical():
            yield OperateMode(IDS.add)
            yield ContentsView(IDS.add)
            yield OperateButtons(IDS.add, btn_dict=OpBtnEnum.op_btn_enum_dict(IDS.add))
        yield SwitchSlider(IDS.add)

    def on_mount(self) -> None:
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.operate_mode_container = self.query_one(
            IDS.add.container.op_mode_q, OperateMode
        )
        self.operate_mode_container.path_arg = CMD.cache.dest_dir
        self.query_exactly_one(FilteredDirTree).path = CMD.cache.dest_dir
        self.contents_view = self.query_one(IDS.add.container.contents_q, ContentsView)
        self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        self.add_review_btn = self.query_one(IDS.add.op_btn.add_review_q, Button)
        self.add_review_btn.disabled = True

    @on(Button.Pressed)
    def refresh_dir_tree(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label in (FlatBtnLabel.refresh_tree, OpBtnLabel.reload):
            self.dir_tree.reload()
            self.dir_tree.refresh()

    @on(DirectoryTree.FileSelected)
    @on(DirectoryTree.DirectorySelected)
    def update_contents_view(
        self, event: DirectoryTree.FileSelected | DirectoryTree.DirectorySelected
    ) -> None:
        event.stop()
        if event.node.data is None:
            raise ValueError("event.node.data is None in update_contents_view")

        if self.add_review_btn.disabled is True:
            self.add_review_btn.disabled = False
        self.contents_view.show_path = event.node.data.path
        self.operate_mode_container.path_arg = event.node.data.path
        self.contents_view.border_title = f" {event.node.data.path.name} "

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.add.switch.unmanaged_dirs:
            self.dir_tree.unmanaged_dirs = event.value
        elif event.switch.id == IDS.add.switch.unwanted:
            self.dir_tree.unwanted = event.value
        self.dir_tree.reload()


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
    def is_unwanted(cls, extension: str) -> bool:
        try:
            cls(extension)
            return True
        except ValueError:
            return "cache" in extension.lower()


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
    def is_unwanted(cls, name: str) -> bool:
        try:
            cls(name)
            return True
        except ValueError:
            return "cache" in name.lower()

    @classmethod
    def is_private_key_name(cls, value: str) -> bool:
        return cls.is_unwanted(value)
