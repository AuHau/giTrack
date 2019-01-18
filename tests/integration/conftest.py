import os
from unittest import mock

import pytest
import pathlib
import git

import gitrack
from gitrack import config as config_module

from . import helpers


@pytest.fixture()
def repo_dir(tmp_path):  # type: (pathlib.Path) -> pathlib.Path
    path = (tmp_path / 'repo_dir').resolve()  # type: pathlib.Path
    (path / '.git' / 'hooks').mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture()
def inited_repo_dir(store, repo_dir):  # type: (pathlib.Path) -> pathlib.Path
    config_module.Store.init_repo(repo_dir)
    return repo_dir


@pytest.fixture()
def store(tmp_path):
    store_path = (tmp_path / 'store').resolve()
    store_path.mkdir(parents=True, exist_ok=True)
    original_storage = os.environ.get('GITRACK_STORAGE')
    os.environ['GITRACK_STORAGE'] = str(store_path)

    yield store_path
    os.environ['GITRACK_STORAGE'] = original_storage


@pytest.fixture()
def cmd(repo_dir, store):
    tmp_repo_dir = repo_dir

    def _cmd(cmd, config='default.config', repo_dir=None, inited=True, git_inited=False):
        if repo_dir is None:
            repo_dir = tmp_repo_dir

        if inited:
            config_module.Store.init_repo(repo_dir)

        os.chdir(str(repo_dir))

        if git_inited:
            (repo_dir / '.git').rmdir()
            git.Repo.init(str(repo_dir))

        helpers.set_config(repo_dir, config)
        return helpers.inner_cmd(cmd)

    return _cmd


@pytest.fixture(scope='session', autouse=True)
def patch_providers():
    with mock.patch.object(gitrack, 'Providers') as _fixture:
        _fixture.return_value = helpers.TestProvidersEnum
        yield
