import pytest
import requests
import textual

# from chezmoi_mousse.gui import MainScreen
from chezmoi_mousse.id_typing import TabStr
from chezmoi_mousse.main_tabs import AddTab, ApplyTab, DoctorTab, ReAddTab

# from chezmoi_mousse.splash import LoadingScreen


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


def test_app_init():
    from chezmoi_mousse.gui import ChezmoiGUI

    app = ChezmoiGUI()
    assert app


@pytest.mark.parametrize(
    "tab_class,tab_str",
    [
        (ApplyTab, TabStr.apply_tab),
        (ReAddTab, TabStr.re_add_tab),
        (AddTab, TabStr.add_tab),
        (DoctorTab, TabStr.doctor_tab),
    ],
)
def test_tab_init_with_tab_str(tab_class: type, tab_str: TabStr) -> None:
    tab = tab_class(tab_str=tab_str)
    assert tab is not None


# @pytest.mark.parametrize("screen_class", [MainScreen, LoadingScreen])
# def test_screen_init(screen_class: type) -> None:
#     screen = screen_class()
#     assert screen is not None
