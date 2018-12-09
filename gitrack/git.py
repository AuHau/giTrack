import git
import pathlib
import typing


def _has_git(check_dir):  # type: (pathlib.Path) -> bool
    for child in check_dir.iterdir():
        if child.is_dir() and child.name == '.git':
            return True

    return False


def get_repo(current_dir=None):  # type: (typing.Optional[pathlib.Path]) -> git.Repo
    if current_dir is None:
        current_dir = pathlib.Path.cwd().resolve()

    if not current_dir.is_dir():
        current_dir = current_dir.parent

    if _has_git(current_dir):
        return git.Repo(str(current_dir))

    # When following IF is true we reached the root of dir tree
    if current_dir == current_dir.parent:
        raise RuntimeError('No Git repo in the directory tree.')

    return get_repo(current_dir.parent)


def intall_hook(repo):  # type: (git.Repo) -> None
    repo_dir = pathlib.Path(repo.git_dir)
    post_commit_file = repo_dir / 'hooks' / 'post-commit'
    new_file = not post_commit_file.exists()
    write_mode = 'w' if new_file else 'a'

    with post_commit_file.open(write_mode) as file:
        if new_file:
            file.writelines('#!/usr/bin/env bash\n')

        file.writelines('\ngitrack hooks post-commit')

    if new_file:
        post_commit_file.chmod(0o740)
