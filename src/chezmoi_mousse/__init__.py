from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
