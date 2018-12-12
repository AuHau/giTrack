from toggl import api, utils

from . import AbstractProvider
from .. import config, exceptions


class TogglProvider(AbstractProvider):

    NAME = 'toggl'

    def __init__(self, gitrack_config):
        self.gitrack_config = gitrack_config
        self.toggl_config = self._bootstrap_toggl_config(gitrack_config)

    def _bootstrap_toggl_config(self, gitrack_config):  # type: (config.Config) -> utils.Config
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

    def start(self):
        api.TimeEntry.start_and_save(created_with='gitrack', config=self.toggl_config)

    def stop(self, description, amend=False):
        entry = api.TimeEntry.objects.current(config=self.toggl_config)  # type: toggl.api.TimeEntry
        entry.description = description
        entry.stop_and_save()

    def add(self, start, stop, description):
        entry = api.TimeEntry(start, stop, description=description, config=self.toggl_config)
        entry.save()
