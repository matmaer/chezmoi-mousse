import requests
import textual
import pytest


def test_textual_version_is_latest():
    current_version = textual.__version__

    try:
        # Fetch the latest release from GitHub API
        response = requests.get(
            "https://api.github.com/repos/Textualize/textual/releases/latest",
            timeout=1,
        )

        # Check for HTTP errors without raising exceptions
        if response.status_code != 200:
            pytest.fail(
                f"Http error while fetching latest version from GitHub: error {response.status_code}"
            )

        try:
            release_data = response.json()
            latest_tag = release_data["tag_name"]
            latest_version = latest_tag.lstrip("v")
        except (KeyError, ValueError) as e:
            pytest.fail(f"Unexpected GitHub API response format: {e}")

        assert (
            current_version == latest_version
        ), f"Update available: {current_version} -> {latest_version}"

    except requests.RequestException:
        pytest.fail("Cannot reach GitHub API.")


def test_if_app_starts():
    from chezmoi_mousse.gui import ChezmoiGUI

    app = ChezmoiGUI()
    assert app


@pytest.mark.parametrize(
    "tab_class,tab_str,constructor_type",
    [
        ("ApplyTab", "apply_tab", "tab_str"),
        ("ReAddTab", "re_add_tab", "tab_str"),
        ("AddTab", "add_tab", "tab_str"),
        ("DoctorTab", "doctor_tab", "id_only"),
        ("LogTab", "log_tab", "rich_log"),
    ],
)
def test_tab_instantiation(
    tab_class: str, tab_str: str, constructor_type: str
) -> None:
    """Test that each tab class can be instantiated."""
    from chezmoi_mousse.main_tabs import (
        ApplyTab,
        ReAddTab,
        AddTab,
        DoctorTab,
        LogTab,
    )
    from chezmoi_mousse.id_typing import TabStr

    tab_class_map: dict[str, type] = {
        "ApplyTab": ApplyTab,
        "ReAddTab": ReAddTab,
        "AddTab": AddTab,
        "DoctorTab": DoctorTab,
        "LogTab": LogTab,
    }

    tab_str_map = {
        "apply_tab": TabStr.apply_tab,
        "re_add_tab": TabStr.re_add_tab,
        "add_tab": TabStr.add_tab,
        "doctor_tab": TabStr.doctor_tab,
        "log_tab": TabStr.log_tab,
    }

    cls = tab_class_map[tab_class]
    tab_str_enum = tab_str_map[tab_str]

    if constructor_type == "id_only":
        tab = cls(id=tab_str_enum.value)
    elif constructor_type == "rich_log":
        tab = cls(id=tab_str_enum.value, highlight=True, max_lines=20000)
    else:  # tab_str
        tab = cls(tab_str=tab_str_enum)

    assert tab is not None


def test_main_screen_instantiation() -> None:
    from chezmoi_mousse.gui import MainScreen

    main_screen = MainScreen()
    assert main_screen is not None


@pytest.mark.parametrize(
    "filter_type,tab_str,filter1,filter2",
    [
        ("apply", "apply_tab", "unchanged", "expand_all"),
        ("add", "add_tab", "unmanaged_dirs", "unwanted"),
    ],
)
def test_filter_slider_instantiation(
    filter_type: str, tab_str: str, filter1: str, filter2: str
) -> None:
    from chezmoi_mousse.containers import FilterSlider
    from chezmoi_mousse.id_typing import TabStr, FilterEnum

    tab_str_map = {"apply_tab": TabStr.apply_tab, "add_tab": TabStr.add_tab}
    filter_map = {
        "unchanged": FilterEnum.unchanged,
        "expand_all": FilterEnum.expand_all,
        "unmanaged_dirs": FilterEnum.unmanaged_dirs,
        "unwanted": FilterEnum.unwanted,
    }

    filter_enums = (filter_map[filter1], filter_map[filter2])
    filter_slider = FilterSlider(tab_str_map[tab_str], filters=filter_enums)
    assert filter_slider is not None


@pytest.mark.parametrize(
    "location,button1,button2,button3",
    [
        ("left", "tree_btn", "list_btn", None),
        ("right", "diff_btn", "contents_btn", "git_log_btn"),
        ("bottom", "apply_file_btn", "cancel_apply_btn", None),
    ],
)
def test_buttons_horizontal_instantiation(
    location: str, button1: str, button2: str, button3: str | None
) -> None:
    from chezmoi_mousse.containers import ButtonsHorizontal
    from chezmoi_mousse.id_typing import TabStr, ButtonEnum, Location

    location_map = {
        "left": Location.left,
        "right": Location.right,
        "bottom": Location.bottom,
    }

    button_map = {
        "tree_btn": ButtonEnum.tree_btn,
        "list_btn": ButtonEnum.list_btn,
        "diff_btn": ButtonEnum.diff_btn,
        "contents_btn": ButtonEnum.contents_btn,
        "git_log_btn": ButtonEnum.git_log_btn,
        "apply_file_btn": ButtonEnum.apply_file_btn,
        "cancel_apply_btn": ButtonEnum.cancel_apply_btn,
    }

    buttons = [button_map[button1], button_map[button2]]
    if button3 is not None:
        buttons.append(button_map[button3])

    buttons_horizontal = ButtonsHorizontal(
        TabStr.apply_tab,
        buttons=tuple(buttons),
        location=location_map[location],
    )
    assert buttons_horizontal is not None


@pytest.mark.parametrize("switcher_type", ["left", "right"])
def test_content_switcher_instantiation(switcher_type: str) -> None:
    from chezmoi_mousse.containers import (
        ContentSwitcherLeft,
        ContentSwitcherRight,
    )
    from chezmoi_mousse.id_typing import TabStr

    if switcher_type == "left":
        switcher = ContentSwitcherLeft(TabStr.apply_tab)
    else:  # right
        switcher = ContentSwitcherRight(TabStr.apply_tab)

    assert switcher is not None


@pytest.mark.parametrize(
    "widget_class,view_id",
    [
        ("AutoWarning", ""),  # AutoWarning doesn't use view_id
        ("ContentsView", "test_contents_view"),
        ("GitLogView", "test_git_log_view"),
    ],
)
def test_widget_instantiation(widget_class: str, view_id: str) -> None:
    from chezmoi_mousse.widgets import AutoWarning, ContentsView, GitLogView

    if widget_class == "AutoWarning":
        widget = AutoWarning()
    elif widget_class == "ContentsView":
        widget = ContentsView(view_id=view_id)
    else:  # GitLogView
        widget = GitLogView(view_id=view_id)

    assert widget is not None


@pytest.mark.parametrize(
    "screen_class", ["CustomScrollBarRender", "AnimatedFade", "LoadingScreen"]
)
def test_screen_instantiation(screen_class: str) -> None:
    from chezmoi_mousse.gui import CustomScrollBarRender
    from chezmoi_mousse.splash import AnimatedFade, LoadingScreen

    if screen_class == "CustomScrollBarRender":
        instance = CustomScrollBarRender()
    elif screen_class == "AnimatedFade":
        instance = AnimatedFade()
    else:  # LoadingScreen
        instance = LoadingScreen()

    assert instance is not None


@pytest.mark.parametrize("tree_path", ["/tmp/test_tree", "/home/user/test"])
def test_filtered_dir_tree_instantiation(tree_path: str) -> None:
    from chezmoi_mousse.widgets import FilteredDirTree

    # FilteredDirTree doesn't depend on chezmoi, just needs a valid path
    tree = FilteredDirTree(tree_path)
    assert tree is not None
