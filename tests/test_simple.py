from unittest.mock import patch
from chezmoi_mousse import main
from chezmoi_mousse.tui import ChezmoiTUI


def test_main_function():
    assert callable(main), "main should be callable"


def test_main_runs_without_errors():
    with patch.object(ChezmoiTUI, "run"):
        try:
            main()
        except Exception as e:
            assert False, f"main() raised an exception: {e}"


def test_main_return_type():
    with patch.object(ChezmoiTUI, "run"):
        result = main()
        assert result is None, "main() should return None"


def test_main_calls_tui_run():
    with patch.object(ChezmoiTUI, "run") as mock_run:
        main()
        mock_run.assert_called_once_with(
            inline=False, headless=False, mouse=True
        )


def test_import_chezmoi_mousse():
    try:
        from chezmoi_mousse import main
    except ImportError:
        assert False, "Failed to import chezmoi_mousse"
