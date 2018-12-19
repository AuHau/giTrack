import abc
import datetime
import typing


class AbstractProvider(abc.ABC):

    support_projects = False
    support_tasks = False

    @classmethod
    @abc.abstractmethod
    def init(cls):  # type: () -> typing.Dict
        pass

    @abc.abstractmethod
    def start(self):  # type: () -> None
        pass

    @abc.abstractmethod
    def stop(self, description, amend=False, task=None,
             project=None):  # type: (str, bool, typing.Union[str, int], typing.Union[str, int]) -> None
        pass

    @abc.abstractmethod
    def add(self, start, stop, description, task=None, project=None):  # type: (datetime.datetime, datetime.datetime, str, typing.Union[str, int], typing.Union[str, int]) -> None
        pass
