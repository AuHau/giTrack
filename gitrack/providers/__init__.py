import abc
import datetime
import time
import typing

from gitrack import config as config_module


class AbstractProvider(abc.ABC):

    support_projects = False
    support_tasks = False

    def __init__(self, config):  # type: (config_module.Config) -> None
        self.config = config

    @classmethod
    @abc.abstractmethod
    def init(cls):  # type: () -> typing.Dict
        pass

    @property
    def _status_file(self):
        return self.config.repo_data_dir / 'status'

    @abc.abstractmethod
    def start(self):  # type: () -> None
        self.config.store['running'] = True
        self.config.store['since'] = datetime.datetime.now()

        self._status_file.write_text(str(int(time.time())))

    @abc.abstractmethod
    def stop(self, description, amend=False, task=None,
             project=None):  # type: (str, bool, typing.Union[str, int], typing.Union[str, int]) -> None
        self.config.store['running'] = False
        self.config.store['since'] = None

        self._status_file.write_text('')

    @abc.abstractmethod
    def add(self, start, stop, description, task=None, project=None):  # type: (datetime.datetime, datetime.datetime, str, typing.Union[str, int], typing.Union[str, int]) -> None
        pass
