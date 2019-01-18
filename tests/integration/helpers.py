import os
import re
import shutil
from enum import Enum

from pathlib import Path

from click.testing import CliRunner

from gitrack import cli
from gitrack.providers import AbstractProvider


def inner_cmd(cmd):  # type: (str) -> ParsingResult

    parsed = re.findall(r"([\"]([^\"]+)\")|([']([^']+)')|(\S+)",
                        cmd)  # Simulates quoting of strings with spaces (eq. filter -n "some important task")
    args = [i[1] or i[3] or i[4] for i in parsed]

    print(os.getcwd())

    result = CliRunner().invoke(cli.cli, args, obj={}, catch_exceptions=False)

    print(result.stdout)

    return result


def set_config(repo_dir, config='default.config'):
    config_path = Path(__file__).parent.parent
    config_path = config_path.joinpath('configs/' + config)

    if not config_path.exists():
        raise ValueError('Unknown config path: ' + str(config_path))

    shutil.copyfile(str(config_path), str(repo_dir / '.gitrack'))


class TestProvider(AbstractProvider):

    @classmethod
    def init(cls):
        pass

    def start(self, force=False):
        super().start(force)

    def stop(self, description, task=None, project=None, force=False):
        super().stop(description, task, project, force)

    def cancel(self):
        super().cancel()


class TestProvidersEnum(Enum):
    TEST = 'test'
    TOGGL = 'toggl'

    def klass(self):
        if self == self.TEST:
            return TestProvider
        elif self == self.TOGGL:
            from gitrack.providers.toggl import TogglProvider
            return TogglProvider

        raise RuntimeError('Unknown provider!')

    def __str__(self):
        return self.value
