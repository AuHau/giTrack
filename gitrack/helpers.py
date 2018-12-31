import re
import shutil

import git
import pathlib
import typing
import click
import inquirer

from gitrack import exceptions, config, Providers, GITRACK_POST_COMMIT_EXECUTABLE_FILENAME, SUPPORTED_SHELLS, TaskParsingModes

CMD_PATH_PLACEHOLDER = '{{CMD_PATH}}'

SHELLS_COMMANDS = {
    'bash': '\n{} &',
    'zsh': '\n{} &',
    'fish': '\n{} & disown',
}


def _folder_has_git(check_dir):  # type: (pathlib.Path) -> bool
    for child in check_dir.iterdir():
        if child.is_dir() and child.name == '.git':
            return True

    return False


def get_repo_dir(current_dir=None):  # type: (typing.Optional[pathlib.Path]) -> pathlib.Path
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
    return config.is_repo_initialized(repo_dir)


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

        raise exceptions.UnknownShell('It seems that the currently used post-commit '
                                      'hook uses shebang that is not known to Gitrack: ' + shebang)


def install_hook(repo_dir):  # type: (pathlib.Path) -> None
    hooks_dir = repo_dir / '.git' / 'hooks'

    if is_hook_installed(hooks_dir):
        return

    _create_gitrack_post_commit_executable(hooks_dir)
    path_to_post_commit_executable = str(hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME)

    post_commit_file = hooks_dir / 'post-commit'
    if post_commit_file.exists():
        shell = _get_shell(post_commit_file)

        with post_commit_file.open('a') as f:
            f.writelines(SHELLS_COMMANDS[shell].format(path_to_post_commit_executable))
    else:
        post_commit_file.write_text('#!/usr/bin/env bash\n\n{} &'.format(path_to_post_commit_executable))
        post_commit_file.chmod(0o740)


def _create_gitrack_post_commit_executable(hooks_dir):  # type: (pathlib.Path) -> None
    gitrack_post_commit_executable = hooks_dir / GITRACK_POST_COMMIT_EXECUTABLE_FILENAME
    gitrack_binary = shutil.which('gitrack')

    with (pathlib.Path(__file__).parent / 'scripts' / 'post_commit_executable_template.sh').open('r') as f:
        template = f.read().replace(CMD_PATH_PLACEHOLDER, gitrack_binary)

    gitrack_post_commit_executable.write_text(template)
    gitrack_post_commit_executable.chmod(0o740)

#####################################################################################
# Initialization
#####################################################################################


def init(repo_dir, config_store_destination, should_install_hook=True,
         verbose=True):  # type: (pathlib.Path, config.ConfigDestination, bool, bool) -> None
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


def prompt_configuration():  # type: () -> typing.Dict
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

