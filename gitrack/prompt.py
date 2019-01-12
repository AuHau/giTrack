import os
import pathlib
import subprocess

import click

from gitrack import exceptions, SUPPORTED_SHELLS, config

_SHELLS_SCELETONS = {
    'bash': {
        'activate': """if [[ ! ${{GITRACK_DATA}} ]];
then
    {}
fi""",
        'deactivate': """if [[ ${{GITRACK_DATA}} ]];
then
    {}
fi""",
        'execute': """if [[ ${{GITRACK_DATA}} ]];
then
    {}
else
    {}
fi""",
    },
    'fish': {
        'activate': """if [ ! $GITRACK_DATA ]
    {}
end""",
        'deactivate': """if [ $GITRACK_DATA ]
    {}
end""",
        'execute': """if [ $GITRACK_DATA ]
    {}
else
    {}
end""",
    },
}


def _get_shell():
    # TODO: [Q] Some more extensive checks? Or Parent is always a shell?
    result = subprocess.run(['ps', '-p', str(os.getppid()), '-o', 'command='], stdout=subprocess.PIPE)
    command = str(result.stdout)

    for supported_shell in SUPPORTED_SHELLS:
        if supported_shell in command:
            return supported_shell

    raise exceptions.UnknownShell('Shell \'{}\' is not supported!'.format(command))


def activate(style):
    """
    Prints shell script to STDOUT that enhance the shell's prompt with giTrack's status indicators.

    :param style: Defines the style of the prompt
    :return:
    """
    data_dir = str(config.get_data_dir() / 'repos')
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_activate.{}.{}'.format(style, shell))  # type: pathlib.Path
    script = activation_file.read_text().replace('{{DATA_PATH}}', data_dir)
    click.echo(_SHELLS_SCELETONS[shell]['activate'].format(script))


def deactivate():
    """
    Prints shell script to STDOUT that removes the prompt's enhancements.

    :return:
    """
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    deactivation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_deactivate.{}'.format(shell))  # type: pathlib.Path
    click.echo(_SHELLS_SCELETONS[shell]['deactivate'].format(deactivation_file.read_text()))


def execute(style):
    """
    Prints shell script to STDOUT that toggl the prompt's enhancements.

    :param style: Defines the style of the prompt
    :return:
    """
    data_dir = str(config.get_data_dir() / 'repos')
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_activate.{}.{}'.format(style, shell))  # type: pathlib.Path
    deactivation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_deactivate.{}'.format(shell))  # type: pathlib.Path

    click.echo(_SHELLS_SCELETONS[shell]['execute'].format(
        deactivation_file.read_text(),
        activation_file.read_text().replace('{{DATA_PATH}}', data_dir),
    ))
