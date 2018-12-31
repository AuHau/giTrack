import os
import pathlib
import psutil

import click

from gitrack import exceptions, SUPPORTED_SHELLS, config


def _get_shell():
    # TODO: [Q] Is psutil dependency really necessary?
    # TODO: [Q] Some more extensive checks? Or Parent is always a shell?
    parent_name = psutil.Process().parent().name()

    for supported_shell in SUPPORTED_SHELLS:
        if supported_shell in parent_name:
            return supported_shell

    raise exceptions.UnknownShell('Shell \'{}\' is not supported!'.format(parent_name))


def is_activated():
    return os.environ.get('GITRACK_DATA') is not None


def activate(mode):
    data_dir = str(config.get_data_dir() / 'repos')
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / ('prompt_activate.{}.{}'.format(mode, shell)) # type: pathlib.Path
    click.echo(activation_file.read_text().replace('{{DATA_PATH}}', data_dir))


def deactivate():
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / ('prompt_deactivate.{}'.format(shell)) # type: pathlib.Path
    click.echo(activation_file.read_text())

