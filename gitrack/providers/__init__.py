import abc
import datetime
import typing


class AbstractProvider(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def init(cls):  # type: () -> typing.Dict
        pass

    @abc.abstractmethod
    def start(self):  # type: () -> None
        pass

    @abc.abstractmethod
    def stop(self, description, amend=False):  # type: (str, bool) -> None
        pass

    @abc.abstractmethod
    def add(self, start, stop, description):  # type: (datetime.datetime, datetime.datetime, str) -> None
        pass
