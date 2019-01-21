import ast
import logging

import inquirer
from toggl import api, utils, exceptions as toggl_exceptions

from gitrack import exceptions
from gitrack.providers import AbstractProvider

logger = logging.getLogger('gitrack.provider.toggl')


class TogglProvider(AbstractProvider):
    support_projects = True
    support_tasks = True

    NAME = 'toggl'

    def __init__(self, config):
        super().__init__(config)
        self.provider_config = self._bootstrap_provider_config()
        self.toggl_config = self._bootstrap_toggl_config()

    def _bootstrap_provider_config(self):
        provider_config = self.config.get_providers_config(self.NAME)

        if 'tags' in provider_config:
            provider_config['tags'] = ast.literal_eval(provider_config['tags'])

        return provider_config

    def _bootstrap_toggl_config(self):  # type: () -> utils.Config
        toggl_config = utils.Config.factory(None)  # type: utils.Config

        if 'api_token' not in self.provider_config:
            raise exceptions.ProviderException(self.NAME, 'Configuration does not contain authentication credentials!')

        toggl_config.api_token = self.provider_config['api_token']

        return toggl_config

    @classmethod
    def init(cls):
        bootstrap = utils.bootstrap.ConfigBootstrap()
        api_token = bootstrap.get_api_token()
        tags = inquirer.shortcuts.text('Should the giTrack\'s entries be tagged? (tags delimited by \',\')')
        tags = tags.split(',')

        return {
            'api_token': api_token,
            'tags': tags,
        }

    def start(self, force=False):
        current = api.TimeEntry.objects.current(config=self.toggl_config)  # type: api.TimeEntry

        if current:
            logger.info("Currently running entry: " + getattr(current, 'description', ''))
            if not force:
                raise exceptions.RunningEntry(self.NAME, 'There is currently running another '
                                                         'time entry which would be overridden!')

        super().start()
        api.TimeEntry.start_and_save(created_with='gitrack', config=self.toggl_config,
                                     tags=self.provider_config.get('tags'))

    def stop(self, description, task=None, project=None, force=False):
        super().stop(description, task, project, force)
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
                    raise exceptions.ProviderException(self.NAME, 'There was an error while fetching the task entity: '
                                                       + e.message)

        if project is not None:
            if isinstance(project, int):
                entry.project = project
            else:
                try:
                    entry.project = api.Project.objects.get(name=project, config=self.toggl_config)
                except (toggl_exceptions.TogglNotFoundException, toggl_exceptions.TogglMultipleResultsException) as e:
                    raise exceptions.ProviderException(self.NAME, 'There was an error while fetching the project entity: ' + e.message)

        entry.stop_and_save()

    def cancel(self):
        super().cancel()

        entry = api.TimeEntry.objects.current(config=self.toggl_config)  # type: api.TimeEntry

        if entry is None:
            return

        entry.delete(config=self.toggl_config)
