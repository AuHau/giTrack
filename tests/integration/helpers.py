import re
import shutil
from enum import Enum

from pathlib import Path

from click.testing import CliRunner

from gitrack import cli, config
from gitrack.providers import AbstractProvider


def inner_cmd(cmd):  # type: (str) -> ParsingResult

    parsed = re.findall(r"([\"]([^\"]+)\")|([']([^']+)')|(\S+)",
                        cmd)  # Simulates quoting of strings with spaces (eq. filter -n "some important task")
    args = [i[1] or i[3] or i[4] for i in parsed]

    result = CliRunner().invoke(cli.cli, args, obj={}, catch_exceptions=False)
    print(result.stdout)  # We want to pytest do the capturing as it will be displayed when tests fail

    return result


def set_config(repo_dir, config='default.config'):
    config_path = Path(__file__).parent.parent
    config_path = config_path.joinpath('configs/' + config)

    if not config_path.exists():
        raise ValueError('Unknown config path: ' + str(config_path))

    shutil.copyfile(str(config_path), str(repo_dir / '.gitrack'))


def repo_data_dir(repo_dir):
    return config.get_data_dir() / 'repos' / config.repo_name(repo_dir)


class ProviderForTesting(AbstractProvider):

    @classmethod
    def init(cls):
        pass

    def start(self, force=False):
        super().start(force)

    def stop(self, description, task=None, project=None, force=False):
        super().stop(description, task, project, force)

    def cancel(self):
        super().cancel()

