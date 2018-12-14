import git
import pathlib
import typing
import click
import inquirer

from . import exceptions, config, PROVIDERS, LOCAL_CONFIG_NAME


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


def install_hook(repo):  # type: (git.Repo) -> None
    repo_dir = pathlib.Path(repo.git_dir)
    post_commit_file = repo_dir / 'hooks' / 'post-commit'
    new_file = not post_commit_file.exists()
    write_mode = 'w' if new_file else 'a'

    with post_commit_file.open(write_mode) as file:
        if new_file:
            file.writelines('#!/usr/bin/env bash')

        # TODO: Usage of correct binary based on using virtualenv/pex/dev environment
        # TODO: Detection of already installed hook
        file.writelines('\n\ngitrack hooks post-commit &')

    if new_file:
        post_commit_file.chmod(0o740)


# TODO: Check if the repo was not already initialized!
def init(repo, config_store_destination, verbose=True):  # type: (git.Repo, config.ConfigDestination, bool) -> None
    if config.Store.is_repo_initialized(repo):
        raise exceptions.InitializedRepoException('Repo has been already initialized!')

    if verbose:
        print_welcome(repo.git_dir)

    repo_configuration = prompt_configuration()

    provider_class = PROVIDERS(repo_configuration['provider']).klass()
    provider_configuration = provider_class.init()

    config.Store.init_repo(repo)

    gitrack_config = config.Config(repo, config_store_destination, **repo_configuration)
    gitrack_config.set_providers_config(repo_configuration['provider'], provider_configuration)
    gitrack_config.persist()

    install_hook(repo)


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
