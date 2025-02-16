# /usr/bin/env bash

# Added after finding out you cannot run this app from withit a
# chezmoi cd subshell.
# Will need to be reviewed when packaging
# This will have something to do with the subprocess CWD which probably uses
# the dir from where the TUI app was started.
# To check how the shell is customized when it comes to environment variables
# when chezmoi cd is run.


# env var CHEZMOI_SUBSHELL=1 can be used

# also add app exit when shutil cannot find the chezmoi command, no exception is raised by shutil.which

# cmd_path = shutil.which("chezmoi")
# if cmd_path is None:
# raise FileNotFoundError(f"Command '{cmd}' not found in PATH")

