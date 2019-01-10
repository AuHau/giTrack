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
        """
        Method called during the `gitrack init` phase after the common options are bootstrapped.
        This method should gather all the configuration from user in interactive manner and process it.
        The result is to be returned as a dict.

        :return: Dict of configuration that will be saved as part of giTrack's configuration
        """
        pass

    @property
    def _status_file(self):
        """
        Text file where is stored the tracking status for the current repo.
        It contains UNIX timestamp of moment when the tracking was started or when the last time entry was created
        in this tracking session.

        :return: pathlib.Path
        :rtype: pathlib.Path
        """
        return self.config.repo_data_dir / 'status'

    @abc.abstractmethod
    def start(self, force=False):  # type: (bool) -> None
        """
        Method called when the user start tracking session, or when commit was detected and the last running was ended
        and a new time entry was started.

        For correct giTrack's functionality, it have to call super().start(...)!

        :param force: If something prevented to create new time entry, this parameter should allow user to
                      override any checks and enforce start of the new time entry.
        :return: None
        """
        self.config.store['running'] = True
        self.config.store['since'] = datetime.datetime.now()

        self._status_file.write_text(str(int(time.time())))

    @abc.abstractmethod
    def stop(self, description, task=None,
             project=None, force=False):  # type: (str, typing.Union[str, int], typing.Union[str, int], bool) -> None
        """
        Method called when a commit was detected and the currently running time entry is supposed be saved.

        For correct giTrack's functionality, it have to call super().stop(...)!

        :param description: The commit message that should serve as description of the time entry.
        :param task: ID or name of the Task that should be assigned to the time entry.
                     Can be ignored if support_tasks==False.
        :param project:ID or name of the Project that should be assigned to the time entry.
                       Can be ignored if support_projects==False.
        :param force: If something prevented to save the current time entry, this parameter should allow user to
                      override any checks and enforce save of the time entry.
        :return: None
        """
        self.config.store['running'] = False
        self.config.store['since'] = None

        self._status_file.write_text('')

    @abc.abstractmethod
    def cancel(self):
        """
        Method should cancel the currently running time entry.

        For correct giTrack's functionality, it have to call super().cancel(...)!

        :return:
        """
        self.config.store['running'] = False
        self.config.store['since'] = None

        self._status_file.write_text('')

