import logging

from toggl import api, utils, exceptions as toggl_exceptions

from gitrack.providers import AbstractProvider
from gitrack import config as config_module, exceptions

logger = logging.getLogger('gitrack.provider.toggl')


class TogglProvider(AbstractProvider):
    support_projects = True
    support_tasks = True

    NAME = 'toggl'

    def __init__(self, config):
        super().__init__(config)
        self.toggl_config = self._bootstrap_toggl_config(self.config)

    def _bootstrap_toggl_config(self, gitrack_config):  # type: (config_module.Config) -> utils.Config
        provider_config = gitrack_config.get_providers_config(self.NAME)
        toggl_config = utils.Config.factory(None)  # type: utils.Config

        if 'api_token' not in provider_config:
            raise exceptions.ProviderException(self.NAME, 'Configuration does not contain authentication credentials!')

        toggl_config.api_token = provider_config['api_token']

        return toggl_config

    @classmethod
    def init(cls):
        bootstrap = utils.bootstrap.ConfigBootstrap()
        api_token = bootstrap._get_api_token()

        return {'api_token': api_token}

    def start(self, force=False):
        current = api.TimeEntry.objects.current(config=self.toggl_config)  # type: api.TimeEntry

        if current:
            logger.info("Currently running entry: " + current.description)
            if not force:
                raise exceptions.ProviderException(self.NAME, 'There is currently running another time entry which would be overridden!')

        super().start()
        api.TimeEntry.start_and_save(created_with='gitrack', config=self.toggl_config)

    def stop(self, description, amend=False, task=None, project=None, force=False):
        super().stop(description, amend, task, project)
        entry = api.TimeEntry.objects.current(config=self.toggl_config)  # type: api.TimeEntry

        if entry is None:
            return

        entry.description = description

        if task is not None:
            if isinstance(task, int):
                entry.task = task
            else:
                try:
                    entry.task = api.Task.objects.get(name=task, config=self.toggl_config)
                except (toggl_exceptions.TogglNotFoundException, toggl_exceptions.TogglMultipleResultsException) as e:
                    raise exceptions.ProviderException(self.NAME, 'There was an error while fetching the task entity: ' + e.message)

        if project is not None:
            if isinstance(project, int):
                entry.project = project
            else:
                try:
                    entry.project = api.Project.objects.get(name=project, config=self.toggl_config)
                except (toggl_exceptions.TogglNotFoundException, toggl_exceptions.TogglMultipleResultsException) as e:
                    raise exceptions.ProviderException(self.NAME, 'There was an error while fetching the project entity: ' + e.message)

        entry.stop_and_save()

    def add(self, start, stop, description, task=None, project=None):
        entry = api.TimeEntry(start, stop, description=description, config=self.toggl_config)

        if task is not None:
            if isinstance(task, int):
                entry.task = task
            else:
                try:
                    entry.task = api.Task.objects.get(name=task, config=self.toggl_config)
                except (toggl_exceptions.TogglNotFoundException, toggl_exceptions.TogglMultipleResultsException) as e:
                    raise exceptions.ProviderException(self.NAME, 'There was an error while fetching the task entity: ' + e.message)

        if project is not None:
            if isinstance(project, int):
                entry.project = project
            else:
                try:
                    entry.project = api.Project.objects.get(name=project, config=self.toggl_config)
                except (toggl_exceptions.TogglNotFoundException, toggl_exceptions.TogglMultipleResultsException) as e:
                    raise exceptions.ProviderException(self.NAME, 'There was an error while fetching the project entity: ' + e.message)

        entry.save()
