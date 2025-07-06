import requests
import textual
import pytest

from chezmoi_mousse.id_typing import TabStr, FilterEnum
from chezmoi_mousse.main_tabs import ApplyTab, ReAddTab, AddTab, DoctorTab
from chezmoi_mousse.widgets import DiffView, ContentsView, GitLogView


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


def test_loading_screen_instantiation() -> None:
    from chezmoi_mousse.splash import LoadingScreen

    instance = LoadingScreen()
    assert instance is not None


def test_splash_screen_instantiation() -> None:
    from chezmoi_mousse.gui import MainScreen

    instance = MainScreen()
    assert instance is not None


@pytest.mark.parametrize(
    "tab_class,tab_str",
    [
        (ApplyTab, TabStr.apply_tab),
        (ReAddTab, TabStr.re_add_tab),
        (AddTab, TabStr.add_tab),
    ],
)
def test_tab_instantiation_with_tab_str(
    tab_class: type, tab_str: TabStr
) -> None:
    tab = tab_class(tab_str=tab_str)
    assert tab is not None


def test_doctor_tab_instantiation() -> None:

    tab = DoctorTab()
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


# @pytest.mark.parametrize("switcher_type", ["left", "right"])
# def test_content_switcher_instantiation(switcher_type: str) -> None:
#     from chezmoi_mousse.containers import (
#         ContentSwitcherLeft,
#         ContentSwitcherRight,
#     )
#     from chezmoi_mousse.id_typing import TabStr

#     if switcher_type == "left":
#         switcher = ContentSwitcherLeft(TabStr.apply_tab)
#     else:  # right
#         switcher = ContentSwitcherRight(TabStr.apply_tab)

#     assert switcher is not None


@pytest.mark.parametrize("widget_class", [DiffView, ContentsView, GitLogView])
def test_view_widget_instantiation(widget_class: type) -> None:
    test_view_id = f"test_{widget_class.__name__.lower()}"

    if widget_class == DiffView:
        widget = widget_class(tab_name=TabStr.apply_tab, view_id=test_view_id)
    else:  # ContentsView and GitLogView
        widget = widget_class(view_id=test_view_id)

    assert widget is not None


def test_scroll_bar_render_instantiation() -> None:
    from chezmoi_mousse.gui import CustomScrollBarRender

    instance = CustomScrollBarRender()
    assert instance is not None


def test_filtered_dir_tree_instantiation() -> None:
    from chezmoi_mousse.widgets import FilteredDirTree

    tree = FilteredDirTree(".")
    assert tree is not None
