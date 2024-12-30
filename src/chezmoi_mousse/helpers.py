import subprocess


def run_chezmoi(params: list) -> subprocess.CompletedProcess:
    """ run a chezmoi command with the given parameters """
    result = subprocess.run(
        ["chezmoi"] + params,
        capture_output=True,
        check=True,
        encoding="utf-8",
        shell=False,
        timeout=1,
    )
    return result
