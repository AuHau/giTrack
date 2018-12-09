import pathlib
import pickle

import git
import appdirs

from . import exceptions

class Store:

    APP_NAME = 'gitrack'

    def __init__(self, repo):  # type: (git.Repo) -> None
        try:
            name = repo.git_dir
        except AttributeError:
            name = str(repo)

        path = pathlib.Path(appdirs.user_data_dir(self.APP_NAME)) / 'repos'
        path.mkdir(parents=True, exist_ok=True)
        self._path = path / name + '.pickle'  # type: pathlib.Path

        if not self._path.exists():
            raise exceptions.UninitializedRepoException('Repo \'{}\' has not been initialized!'.format(name))

        self.data = {}

    def load(self):
        with self._path.open('r') as file:
            self.data = pickle.load(file)

    def save(self):
        with self._path.open('w') as file:
            pickle.dump(self.data, file)
