from enum import StrEnum

from chezmoi_mousse._chars import Chars


class OperateHelp(StrEnum):
    add = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
    apply_file = "[$text-primary]The file in the destination directory will be modified.[/]"
    # apply_dir = "[$text-primary]The directory in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    destroy_file = "[$text-error]Permanently remove the file both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    # destroy_dir = "[$text-error]Permanently remove the directory both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = "[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_file = "[$text-primary]Remove the file from the source state, i.e. stop managing them.[/]"
    # forget_dir = "[$text-primary]Remove the directory from the source state, i.e. stop managing them.[/]"
    re_add_file = (
        "[$text-primary]Overwrite the source state with current local file[/]"
    )
    # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"
