"""Singleton to store output for each command in the ChezmoiCommands class"""

CHEZMOI = {
    "data": dict(),
    "dump_config": dict(),
    "cat_config": dict(),
    "doctor": dict(),
    "ignored": dict(),
    "managed": dict(),
    "unmanaged": dict(),
}