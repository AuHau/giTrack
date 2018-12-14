from enum import Enum


APP_NAME = 'gitrack'
LOCAL_CONFIG_NAME = '.gitrack'
GITRACK_POST_COMMIT_EXECUTABLE_FILENAME = 'post-commit.gitrack'
SUPPORTED_SHELLS = ('bash', 'zsh', 'fish')


class PROVIDERS(Enum):

    TOGGL = 'toggl'

    def klass(self):
        if self == self.TOGGL:
            from .providers.toggl import TogglProvider
            return TogglProvider

        raise RuntimeError('Unknown provider!')
