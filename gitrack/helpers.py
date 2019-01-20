import re
import shutil

import git
import pathlib
import typing
import click
import inquirer
import requests

from gitrack import exceptions, config, Providers, GITRACK_POST_COMMIT_EXECUTABLE_FILENAME, SUPPORTED_SHELLS, TaskParsingModes, __version__, GITHUB_REPO_NAME

CMD_PATH_PLACEHOLDER = '{{CMD_PATH}}'

SHELLS_COMMANDS = {
    'bash': '\n{} &',
    'zsh': '\n{} &',
    'fish': '\n{} & disown',
}


def _folder_has_git(check_dir):  # type: (pathlib.Path) -> bool
    """
    Check if directory contains Git metadata folder

    :param check_dir: Directory to check
    :return: True if .git folder is present
    """
    for child in check_dir.iterdir():
        if child.is_dir() and child.name == '.git':
            return True

    return False


def get_repo_dir(current_dir=None):  # type: (typing.Optional[pathlib.Path]) -> pathlib.Path
    """
    Recursively travers the folder tree in search for root of Git repo. (eq. folder that contains .git folder)
    Does not detects git submodules.

    :param current_dir: Starting point of the traversal, if None that current working directory is used.
    :return:
    :raises RuntimeError: If no .git folder is found.
    """
    if current_dir is None:
        current_dir = pathlib.Path.cwd().resolve()

    if not current_dir.is_dir():
        current_dir = current_dir.parent

    if _folder_has_git(current_dir):
        return current_dir

    # When following IF is true we reached the root of dir tree
    if current_dir == current_dir.parent:
        raise RuntimeError('No Git repo in the directory tree.')

    return get_repo_dir(current_dir.parent)


def is_repo_initialized(repo_dir):  # type: (pathlib.Path) -> bool
    """
    Detects if repo defined by repo_dir has been already initialized for giTrack usage.

    :param repo_dir:
    :return:
    """
    return config.is_repo_initialized(repo_dir)


def is_hook_installed(hooks_dir):  # type:(pathlib.Path) -> bool
    """
    Detects if Git hook was installed in the hook's folder. This detects only hook installed directly by
    giTrack. If the user opted-out for automatic installation and performed manual integration, then this function
    won't detect that.

    :param hooks_dir: .git/hooks/ folder
    :return:
    """
    return (hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME).exists()


def _get_scripts_shell(script_file):  # type: (pathlib.Path) -> str
    """
    Returns the shell used in the passed script file. If no shell is recognized exception is raised.
    Depended on presence of shebang.

    Supported shells: Bash, Fish, Zsh

    :param script_file:
    :return:
    :raises exceptions.UnknownShell: If no shell is recognized
    """
    with script_file.open('r') as f:
        shebang = f.readline().lower()

        for shell in SUPPORTED_SHELLS:
            if shell in shebang:
                return shell

        raise exceptions.UnknownShell('It seems that the currently used post-commit '
                                      'hook uses shebang that is not known to Gitrack: ' + shebang)


def install_hook(repo_dir):  # type: (pathlib.Path) -> None
    """
    Will automatically install Git's hook post-commit for detecting new commits.

    Function detects if post-commit script is already present and if so, it tries to only add the relevant piece
    for giTrack's need.

    It uses absolute paths, so if the repo is moved it will stop work.

    :param repo_dir:
    :return:
    """
    hooks_dir = repo_dir / '.git' / 'hooks'

    if is_hook_installed(hooks_dir):
        return

    _create_gitrack_post_commit_executable(hooks_dir)
    path_to_post_commit_executable = str(hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME)

    post_commit_file = hooks_dir / 'post-commit'
    if post_commit_file.exists():
        shell = _get_scripts_shell(post_commit_file)

        with post_commit_file.open('a') as f:
            f.writelines(SHELLS_COMMANDS[shell].format(path_to_post_commit_executable))
    else:
        post_commit_file.write_text('#!/usr/bin/env bash\n\n{} &'.format(path_to_post_commit_executable))
        post_commit_file.chmod(0o740)


def _create_gitrack_post_commit_executable(hooks_dir):  # type: (pathlib.Path) -> None
    gitrack_post_commit_executable = hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME
    gitrack_binary = shutil.which('gitrack')

    if gitrack_binary is None:
        raise RuntimeError('gitrack binary can not be found!')

    with (pathlib.Path(__file__).parent / 'scripts' / 'post_commit_executable_template.sh').open('r') as f:
        template = f.read().replace(CMD_PATH_PLACEHOLDER, gitrack_binary)

    gitrack_post_commit_executable.write_text(template)
    gitrack_post_commit_executable.chmod(0o740)

#####################################################################################
# Initialization
#####################################################################################


def init(repo_dir, config_store_destination, should_install_hook=True,
         verbose=True):  # type: (pathlib.Path, config.ConfigDestination, bool, bool) -> None
    """
    Initialize Git repo defined by repo_dir for usage with giTrack.

    :param repo_dir:
    :param config_store_destination: Define to which Config's Source will be the bootstrapped configuration stored.
    :param should_install_hook: Define if the automatic installation should happen or not
    :param verbose: How much should the bootstrap be verbose?
    :return:
    """

    if config.is_repo_initialized(repo_dir):
        raise exceptions.InitializedRepoException('Repo has been already initialized!')

    # Initializing repo with .gitrack file ==> no need to bootstrap
    if config.Config.get_local_config_file(repo_dir).exists():
        click.secho('Found local .gitrack file. Skipping bootstrap and using its configuration.', fg='yellow')
        config.Store.init_repo(repo_dir)

        should_install_hook and install_hook(repo_dir)
        return

    if verbose:
        print_welcome(repo_dir)

    repo_configuration = prompt_configuration()

    click.secho('\nNow provider\'s configuration:', fg='white', dim=1)
    provider_class = repo_configuration['provider']
    provider_configuration = provider_class.init()

    config.Store.init_repo(repo_dir)

    repo_configuration['provider'] = provider_class.NAME
    gitrack_config = config.Config(repo_dir, config_store_destination, **repo_configuration)
    gitrack_config.set_providers_config(provider_class.NAME, provider_configuration)
    gitrack_config.persist()

    should_install_hook and install_hook(repo_dir)


def print_welcome(repo_path):
    click.secho("""       _ _____                _    
  __ _(_)__   \_ __ __ _  ___| | __
 / _` | | / /\/ '__/ _` |/ __| |/ /
| (_| | |/ /  | | | (_| | (__|   < 
 \__, |_|\/   |_|  \__,_|\___|_|\_\\
 |___/                             
 \n""", fg='white', dim=True)

    click.echo('Welcome to giTrack! \nLet us initialize giTrack for this repo: {}\n'.format(repo_path))


def _validate_regex(regex):  # type: (str) -> bool
    try:
        re.compile(regex)

        # Regex needs to define named capturing group 'task'
        return '?P<task>' in regex
    except re.error:
        return False


# TODO: [Feature/Medium] When local config is present it should either prepopulate the answers or ask only questions
#  that are not incorporated in the local config
def prompt_configuration():  # type: () -> typing.Dict
    """
    Runs the interactive configuration bootstrap.

    This function runs only the generic giTrack's configuration, not the provider's part.
    :return:
    """
    providers = {provider.value.capitalize(): provider.value for provider in Providers}
    selected_provider = inquirer.shortcuts.list_input('Select provider you want to use for this repo',
                                                      choices=providers.keys())
    selected_provider = Providers(providers[selected_provider]).klass()

    questions = []

    if selected_provider.support_projects:
        questions += [
            inquirer.Confirm('project_support', default=False, message='Enable Project\'s support?'),
            inquirer.Text('project', ignore=lambda x: not x['project_support'], message='Specify project\'s name or ID',
                          validate=lambda _, x: bool(x)),
        ]

    if selected_provider.support_tasks:
        questions += [
            inquirer.Confirm('tasks_support', default=False, message='Enable Task\'s support?'),
            inquirer.List('tasks_mode', message='How should task\'s ID/Name should be retrieved?',
                          choices=TaskParsingModes.messages().values(), ignore=lambda x: not x['tasks_support']),
            inquirer.Text('tasks_value', validate=lambda _, x: bool(x), message='Specify task\'s name or ID',
                          ignore=lambda x: not x['tasks_support'] or x['tasks_mode'] != TaskParsingModes.STATIC.message()),
            inquirer.Text('tasks_regex', validate=lambda _, x: bool(x) and _validate_regex(x),
                          ignore=lambda x: not x['tasks_support'] or x['tasks_mode'] == TaskParsingModes.STATIC.message(),
                          message='Specify Python\'s Regex that will parse the task\'s name or ID. Regex have to have capturing group with name \'task\''),
        ]

    answers = inquirer.prompt(questions)
    if answers is None:
        click.secho("We were not able to setup the needed configuration and we are unfortunately not able to "
                    "proceed without it.", bg="white", fg="red")
        exit(1)

    answers.update({'provider': selected_provider})

    return answers

#####################################################################################
# Task/Projects
#####################################################################################


def _parse_string(regex, string):
    match = re.search(regex, string)

    if not match:
        return None

    return match.group('task')


def get_task(config, repo):  # type: (config.Config, git.Repo) -> typing.Union[str, int]
    """
    For given repository parse task identificator.

    Three modes are supported: static, dynamic message and dynamic branch.
    Static mode will always return value that was defined by user during configuration bootstrap.
    Dynamic message will parse the last commit's message.
    Dynamic branch will parse the current branch name.

    :param config:
    :param repo:
    :return:
    """
    if config.tasks_mode == TaskParsingModes.STATIC:
        return config.tasks_value

    if config.tasks_mode == TaskParsingModes.DYNAMIC_MESSAGE:
        text_to_parse = repo.head.commit.message.strip()
    elif config.tasks_mode == TaskParsingModes.DYNAMIC_BRANCH:
        text_to_parse = repo.active_branch.name
    else:
        raise exceptions.GitrackException('Unkown Task\'s mode: ' + config.tasks_mode)

    task = _parse_string(config.tasks_regex, text_to_parse)

    try:
        return int(task)
    except ValueError:
        return task

#####################################################################################
# Version detection
#####################################################################################


def get_latest_version(repo):
    r = requests.get("https://api.github.com/repos/{}/releases/latest".format(repo))
    return r.json().get('tag_name')


def check_version():
    latest_version = get_latest_version(GITHUB_REPO_NAME)

    if latest_version is None:
        return

    if latest_version != __version__:
        click.secho("There is newer version of gitrack available! "
                    "You are running {}, but there is {}!".format(__version__, latest_version), fg='yellow')



