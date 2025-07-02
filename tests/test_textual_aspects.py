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
