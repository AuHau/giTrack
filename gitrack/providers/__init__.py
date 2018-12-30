import abc
import datetime
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

    @abc.abstractmethod
    def start(self):  # type: () -> None
        self.config.store['running'] = True
        self.config.store['since'] = datetime.datetime.now()

    @abc.abstractmethod
    def stop(self, description, amend=False, task=None,
             project=None):  # type: (str, bool, typing.Union[str, int], typing.Union[str, int]) -> None
        self.config.store['running'] = False
        self.config.store['since'] = None

    @abc.abstractmethod
    def add(self, start, stop, description, task=None, project=None):  # type: (datetime.datetime, datetime.datetime, str, typing.Union[str, int], typing.Union[str, int]) -> None
        pass
