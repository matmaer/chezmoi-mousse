from unittest.mock import patch

from chezmoi_mousse.__main__ import main


def test_main_calls_app_run():
    # Mock the ChezmoiTUI class and its run method
    with patch("chezmoi_mousse.__main__.ChezmoiTUI") as MockChezmoiTUI:
        mock_app = MockChezmoiTUI.return_value
        main()
        # Ensure the ChezmoiTUI class was instantiated
        MockChezmoiTUI.assert_called_once()
        # Ensure the run method was called with the correct arguments
        mock_app.run.assert_called_once_with(
            inline=False, headless=False, mouse=True
        )
