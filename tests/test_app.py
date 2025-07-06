import requests
import textual
import pytest

from chezmoi_mousse.id_typing import (
    ButtonEnum,
    Location,
    TabStr,
    FilterEnum,
    ViewStr,
)


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
    "tab_class,tab_str",
    [
        ("ApplyTab", TabStr.apply_tab),
        ("ReAddTab", TabStr.re_add_tab),
        ("AddTab", TabStr.add_tab),
    ],
)
def test_tab_instantiation_with_tab_str(
    tab_class: str, tab_str: TabStr
) -> None:
    """Test that tab classes with tab_str constructor can be instantiated."""
    from chezmoi_mousse.main_tabs import ApplyTab, ReAddTab, AddTab

    tab_class_map: dict[str, type] = {
        "ApplyTab": ApplyTab,
        "ReAddTab": ReAddTab,
        "AddTab": AddTab,
    }

    cls = tab_class_map[tab_class]
    tab = cls(tab_str=tab_str)
    assert tab is not None


@pytest.mark.parametrize("tab_str", [TabStr.doctor_tab])
def test_doctor_tab_instantiation(tab_str: TabStr) -> None:
    from chezmoi_mousse.main_tabs import DoctorTab

    tab = DoctorTab(id=tab_str.value)
    assert tab is not None


def test_main_screen_instantiation() -> None:
    from chezmoi_mousse.gui import MainScreen

    main_screen = MainScreen()
    assert main_screen is not None


@pytest.mark.parametrize(
    "tab_str,filter1,filter2",
    [
        (TabStr.apply_tab, FilterEnum.unchanged, FilterEnum.expand_all),
        (TabStr.add_tab, FilterEnum.unmanaged_dirs, FilterEnum.unwanted),
    ],
)
def test_filter_slider_instantiation(
    tab_str: TabStr, filter1: FilterEnum, filter2: FilterEnum
) -> None:
    from chezmoi_mousse.containers import FilterSlider

    filter_enums = (filter1, filter2)
    filter_slider = FilterSlider(tab_str, filters=filter_enums)
    assert filter_slider is not None


@pytest.mark.parametrize(
    "location,button1,button2",
    [
        (Location.left, ButtonEnum.tree_btn, ButtonEnum.list_btn),
        (
            Location.bottom,
            ButtonEnum.apply_file_btn,
            ButtonEnum.cancel_apply_btn,
        ),
    ],
)
def test_two_buttons_horizontal(
    location: Location, button1: ButtonEnum, button2: ButtonEnum
) -> None:
    from chezmoi_mousse.containers import ButtonsHorizontal
    from chezmoi_mousse.id_typing import TabStr

    buttons = [button1, button2]

    buttons_horizontal = ButtonsHorizontal(
        TabStr.apply_tab, buttons=tuple(buttons), location=location
    )
    assert buttons_horizontal is not None


@pytest.mark.parametrize(
    "location,button1,button2,button3",
    [
        (
            Location.right,
            ButtonEnum.diff_btn,
            ButtonEnum.contents_btn,
            ButtonEnum.git_log_btn,
        )
    ],
)
def test_three_buttons_horizontal(
    location: Location,
    button1: ButtonEnum,
    button2: ButtonEnum,
    button3: ButtonEnum,
) -> None:
    from chezmoi_mousse.containers import ButtonsHorizontal
    from chezmoi_mousse.id_typing import TabStr

    buttons = [button1, button2, button3]

    buttons_horizontal = ButtonsHorizontal(
        TabStr.apply_tab, buttons=tuple(buttons), location=location
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
    "view_type",
    [ViewStr.diff_view, ViewStr.contents_view, ViewStr.git_log_view],
)
def test_view_widget_instantiation(view_type: ViewStr) -> None:
    from chezmoi_mousse.widgets import DiffView, ContentsView, GitLogView
    from typing import Any

    # Direct mapping from ViewStr to widget classes
    widget_map: dict[ViewStr, type[Any]] = {
        ViewStr.diff_view: DiffView,
        ViewStr.contents_view: ContentsView,
        ViewStr.git_log_view: GitLogView,
    }

    cls = widget_map[view_type]
    test_view_id = f"test_{view_type.value}"

    if view_type == ViewStr.diff_view:
        widget = cls(tab_name=TabStr.apply_tab, view_id=test_view_id)
    else:
        widget = cls(view_id=test_view_id)

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
