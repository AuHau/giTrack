from enum import Enum
from pbr.version import VersionInfo

VERSION = VersionInfo('gitrack').semantic_version()
__version__ = VERSION.release_string()

GITHUB_REPO_NAME = 'auhau/gitrack'
APP_NAME = 'gitrack'
LOCAL_CONFIG_NAME = '.gitrack'
GITRACK_POST_COMMIT_EXECUTABLE_FILENAME = 'post-commit.gitrack'
SUPPORTED_SHELLS = ('bash', 'zsh', 'fish')


class Providers(Enum):

    TOGGL = 'toggl'

    def klass(self):
        if self == self.TOGGL:
            from .providers.toggl import TogglProvider
            return TogglProvider

        raise RuntimeError('Unknown provider!')

    def __str__(self):
        return self.value


class TaskParsingModes(Enum):
    STATIC = 'static'
    DYNAMIC_BRANCH = 'dynamic_branch'
    DYNAMIC_MESSAGE = 'dynamic_message'

    @classmethod
    def messages(cls):
        return {
            cls.STATIC: 'static value',
            cls.DYNAMIC_BRANCH: 'dynamically parsed from branch name',
            cls.DYNAMIC_MESSAGE: 'dynamically parsed from commit message',
        }

    def message(self):
        return self.messages()[self]
