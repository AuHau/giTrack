import os
import pathlib
import psutil

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
    # TODO: [Q] Is psutil dependency really necessary?
    # TODO: [Q] Some more extensive checks? Or Parent is always a shell?
    parent_name = psutil.Process().parent().name()

    for supported_shell in SUPPORTED_SHELLS:
        if supported_shell in parent_name:
            return supported_shell

    raise exceptions.UnknownShell('Shell \'{}\' is not supported!'.format(parent_name))


def activate(mode):
    data_dir = str(config.get_data_dir() / 'repos')
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_activate.{}.{}'.format(mode, shell))  # type: pathlib.Path
    script = activation_file.read_text().replace('{{DATA_PATH}}', data_dir)
    click.echo(_SHELLS_SCELETONS[shell]['activate'].format(script))


def deactivate():
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    deactivation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_deactivate.{}'.format(shell))  # type: pathlib.Path
    click.echo(_SHELLS_SCELETONS[shell]['deactivate'].format(deactivation_file.read_text()))


def execute(mode):
    data_dir = str(config.get_data_dir() / 'repos')
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_activate.{}.{}'.format(mode, shell))  # type: pathlib.Path
    deactivation_file = pathlib.Path(__file__).parent / 'scripts' / (
        'prompt_deactivate.{}'.format(shell))  # type: pathlib.Path

    click.echo(_SHELLS_SCELETONS[shell]['execute'].format(
        deactivation_file.read_text(),
        activation_file.read_text().replace('{{DATA_PATH}}', data_dir),
    ))
