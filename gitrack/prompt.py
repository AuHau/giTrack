import os
import pathlib
import shutil
import psutil

import click

from . import exceptions, SUPPORTED_SHELLS


def _get_shell():
    # TODO: [Q] Is psutil dependency really necessary?
    # TODO: [Q] Some more extensive checks? Or Parent is always a shell?
    parent_name = psutil.Process().parent().name()

    for supported_shell in SUPPORTED_SHELLS:
        if supported_shell in parent_name:
            return supported_shell

    raise exceptions.UnknownShell('Shell \'{}\' is not supported!'.format(parent_name))


def is_activated():
    return os.environ.get('GITRACK_CMD') is not None


def activate(mode):
    gitrack_binary = shutil.which('gitrack-status')
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / ('prompt_activate.{}.{}'.format(mode, shell)) # type: pathlib.Path
    click.echo(activation_file.read_text().replace('{{CMD_PATH}}', gitrack_binary))


def deactivate():
    shell = _get_shell()

    # ZSH and Bash are same for us
    if shell == 'zsh':
        shell = 'bash'

    activation_file = pathlib.Path(__file__).parent / 'scripts' / ('prompt_deactivate.{}'.format(shell)) # type: pathlib.Path
    click.echo(activation_file.read_text())

