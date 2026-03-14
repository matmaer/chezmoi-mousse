"""Compatibility wrapper to allow running the package via a plain script name."""

from .launcher import run_app


def main() -> None:
    run_app()


if __name__ == "__main__":
    main()
