from collections.abc import Callable, Iterable
from enum import StrEnum
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Button, DirectoryTree, Label, Static, Switch

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

__all__ = ["AddTab"]


class AddTabContentsView(ContentsView):

    show_path: reactive["Path | None"] = reactive(None)

    def on_mount(self) -> None:
        self.show_path = CMD.cache.dest_dir

    def _cache_add_dir_contents(self, dir_path: Path) -> None:
        widgets: list[Static | Label] = []
        if dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            widgets.append(
                Static("<- Click a path to see its contents.", classes=Tcss.added)
            )
        unmanaged_dirs: list[str] = sorted(
            [
                str(p.relative_to(CMD.cache.dest_dir))
                for p in list(dir_path.iterdir())
                if p not in CMD.cache.managed_dir_paths and p.is_dir()
            ]
        )
        unmanaged_files: list[str] = sorted(
            [
                str(p.relative_to(CMD.cache.dest_dir))
                for p in list(dir_path.iterdir())
                if p not in CMD.cache.managed_file_paths and p.is_file()
            ]
        )
        if unmanaged_dirs:
            widgets.append(
                Label("Contains unmanaged directories", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_dirs), classes=Tcss.info))
        if unmanaged_files:
            widgets.append(
                Label("Contains unmanaged files", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_files), classes=Tcss.info))
        if not unmanaged_dirs and not unmanaged_files:
            widgets.append(Static("No unmanaged paths in this directory."))
        self.container_cache[dir_path] = ScrollableContainer(*widgets)
        self.current_container_path = dir_path

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return

        # Hide the previously displayed container
        if self.current_container_path is not None:
            previous_container = self.container_cache.get(
                self.current_container_path, None
            )
            if previous_container is not None:
                previous_container.display = False

        is_mounted = show_path in self.container_cache
        if is_mounted:
            self.container_cache[show_path].display = True
            self.current_container_path = show_path
            return

        if show_path == CMD.cache.dest_dir or show_path.is_dir():
            self._cache_add_dir_contents(show_path)
            self.mount(self.container_cache[show_path])
            self.current_container_path = show_path
        elif show_path.is_file():
            self._cache_file_contents(show_path)
            self.mount(self.container_cache[show_path])
            self.current_container_path = show_path


class AddTab(Horizontal, AppType):

    def __init__(self) -> None:
        super().__init__()
        self.op_btn_dict = OpBtnEnum.op_btn_enum_dict(IDS.add)

    def compose(self) -> ComposeResult:
        yield Vertical(
            FilteredDirTree(CMD.cache.dest_dir),
            Button(label=FlatBtnLabel.refresh_tree, classes=Tcss.refresh_button),
            id=IDS.add.container.left_side,
            classes=Tcss.tab_left_vertical,
        )
        with Vertical():
            yield AddTabContentsView(IDS.add)
            yield OperateButtons(IDS.add, btn_dict=self.op_btn_dict)
        yield SwitchSlider(IDS.add)

    def on_mount(self) -> None:
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.query_exactly_one(FilteredDirTree).path = CMD.cache.dest_dir
        self.contents_view = self.query_one(
            IDS.add.container.contents_q, AddTabContentsView
        )
        self.contents_view.border_title = f" {CMD.cache.dest_dir} "
        self.add_review_btn = self.query_one(IDS.add.op_btn.add_review_q, Button)
        self.add_review_btn.disabled = True

    @on(Button.Pressed)
    def refresh_dir_tree(self, event: Button.Pressed) -> None:
        event.stop()
        self.contents_view.container_cache.clear()
        self.contents_view.show_path = CMD.cache.dest_dir
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
        self.contents_view.border_title = f" {event.node.data.path.name} "
        # Set path_arg for the btn_enums in OperateMode
        for btn_enum in self.op_btn_dict.values():
            if isinstance(btn_enum, OpBtnEnum):
                btn_enum.path_arg = event.node.data.path

    @on(Switch.Changed)
    def handle_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.add.switch.unmanaged_dirs:
            self.dir_tree.unmanaged_dirs = event.value
        elif event.switch.id == IDS.add.switch.unwanted:
            self.dir_tree.unwanted = event.value
        self.dir_tree.reload()


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
                    and self._has_unmanaged_paths_in(p)
                )
                or (
                    p.is_file()
                    and not UnwantedFileExtensions.is_unwanted(p)
                    and not UnwantedFileNames.is_unwanted(p)
                    and p.parent in CMD.cache.managed_dir_paths
                    and p not in CMD.cache.managed_file_paths
                    and self._file_of_interest(p)
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
                    and not UnwantedFileExtensions.is_unwanted(p)
                    and not UnwantedFileNames.is_unwanted(p)
                    and (
                        p.parent in CMD.cache.managed_dir_paths
                        or self._has_unmanaged_paths_in(p.parent)
                    )
                    and p not in CMD.cache.managed_file_paths
                    and self._file_of_interest(p)
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
                )
            ),
            # switches: Green - Green, include all unmanaged paths
            (True, True): lambda p: (
                (p.is_dir() and self._has_unmanaged_paths_in(p))
                or (p.is_file() and p not in CMD.cache.managed_file_paths)
            ),
        }

        # Select the condition based on switches and filter
        key = (self.unmanaged_dirs, self.unwanted)
        return (p for p in paths if conditions[key](p))

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
                        p not in CMD.cache.managed_file_paths
                        and self._file_of_interest(p)
                    ):
                        return True
                elif (
                    p.is_dir()
                    and not UnwantedDirs.is_unwanted(p.name)
                    and self._has_unmanaged_paths_in(p)
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
