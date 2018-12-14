import shutil

import git
import pathlib
import typing
import click
import inquirer

from . import exceptions, config, PROVIDERS, GITRACK_POST_COMMIT_EXECUTABLE_FILENAME, SUPPORTED_SHELLS


CMD_PATH_PLACEHOLDER = '{{CMD_PATH}}'

SHELLS_COMMANDS = {
    'bash': '\n./{} &',
    'zsh': '\n./{} &',
    'fish': '\n./{} & disown',
}


def _folder_has_git(check_dir):  # type: (pathlib.Path) -> bool
    for child in check_dir.iterdir():
        if child.is_dir() and child.name == '.git':
            return True

    return False


def get_repo(current_dir=None):  # type: (typing.Optional[pathlib.Path]) -> git.Repo
    if current_dir is None:
        current_dir = pathlib.Path.cwd().resolve()

    if not current_dir.is_dir():
        current_dir = current_dir.parent

    if _folder_has_git(current_dir):
        return git.Repo(str(current_dir))

    # When following IF is true we reached the root of dir tree
    if current_dir == current_dir.parent:
        raise RuntimeError('No Git repo in the directory tree.')

    return get_repo(current_dir.parent)


def is_repo_initialized(repo):  # type: (git.Repo) -> bool
    return config.Store.is_repo_initialized(repo)


def is_hook_installed(hooks_dir):  # type:(pathlib.Path) -> bool
    return (hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME).exists()


def _get_shell(post_commit_file):  # type: (pathlib.Path) -> str
    """
    Check whether existing post_commit file is a shell script of supported shell if not exception is raised.

    Supported shells: Bash, Fish, Zsh

    :param post_commit_file:
    :return:
    """
    with post_commit_file.open('r') as f:
        shebang = f.readline().lower()

        for shell in SUPPORTED_SHELLS:
            if shell in shebang:
                return shell

        raise exceptions.UnkownShell('It seems that the currently used post-commit '
                                     'hook uses shebang that is not known to Gitrack: ' + shebang)


def install_hook(repo):  # type: (git.Repo) -> None
    hooks_dir = pathlib.Path(repo.git_dir) / 'hooks'

    if is_hook_installed(hooks_dir):
        return

    _create_gitrack_post_commit_executable(hooks_dir)

    post_commit_file = hooks_dir / 'post-commit'
    if post_commit_file.exists():
        shell = _get_shell(post_commit_file)

        with post_commit_file.open('a') as f:
            f.writelines(SHELLS_COMMANDS[shell].format(GITRACK_POST_COMMIT_EXECUTABLE_FILENAME))
    else:
        post_commit_file.write_text('#!/usr/bin/env bash\n\n./{} &'.format(GITRACK_POST_COMMIT_EXECUTABLE_FILENAME))
        post_commit_file.chmod(0o740)


def _create_gitrack_post_commit_executable(hooks_dir):  # type: (pathlib.Path) -> None
    gitrack_post_commit_executable = hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME
    gitrack_binary = shutil.which('gitrack')

    with (pathlib.Path(__file__).parent / 'post_commit_executable_template.sh').open('r') as f:
        template = f.read().replace(CMD_PATH_PLACEHOLDER, gitrack_binary)

    gitrack_post_commit_executable.write_text(template)
    gitrack_post_commit_executable.chmod(0o740)


def init(repo, config_store_destination, should_install_hook=True,
         verbose=True):  # type: (git.Repo, config.ConfigDestination, bool, bool) -> None
    if config.Store.is_repo_initialized(repo):
        raise exceptions.InitializedRepoException('Repo has been already initialized!')

    # Initializing repo with .gitrack file ==> no need to bootstrap
    if config.Config.get_local_config_file(repo).exists():
        config.Store.init_repo(repo)

        should_install_hook and install_hook(repo)
        return

    if verbose:
        print_welcome(repo.git_dir)

    repo_configuration = prompt_configuration()

    provider_class = PROVIDERS(repo_configuration['provider']).klass()
    provider_configuration = provider_class.init()

    config.Store.init_repo(repo)

    gitrack_config = config.Config(repo, config_store_destination, **repo_configuration)
    gitrack_config.set_providers_config(repo_configuration['provider'], provider_configuration)
    gitrack_config.persist()

    should_install_hook and install_hook(repo)


def print_welcome(repo_path):
    click.secho("""       _ _____                _    
  __ _(_)__   \_ __ __ _  ___| | __
 / _` | | / /\/ '__/ _` |/ __| |/ /
| (_| | |/ /  | | | (_| | (__|   < 
 \__, |_|\/   |_|  \__,_|\___|_|\_\\
 |___/                             
 \n""", fg='white', dim=True)

    click.echo('Welcome to giTrack! \nLet us initialize giTrack for this repo: {}\n'.format(repo_path))


def prompt_configuration():  # type: () -> typing.Dict
    providers = {provider.value.capitalize(): provider.value for provider in PROVIDERS}
    selected_provider = inquirer.shortcuts.list_input('Select provider you want to use for this repo',
                                                      choices=providers.keys())

    return {'provider': providers[selected_provider]}
