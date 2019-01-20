import pathlib
from unittest import mock

import git

from .helpers import repo_data_dir, ProviderForTesting


class TestHooks:
    def test_basic(self, cmd, mocker):
        result, repo_dir = cmd('init', inited=False, git_inited=True)

        some_file = (repo_dir / 'some-file')  # type: pathlib.Path
        some_file.write_text('Some text')

        git.Repo(str(repo_dir))

