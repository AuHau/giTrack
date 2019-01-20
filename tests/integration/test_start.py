from time import sleep

from gitrack import config
from .helpers import repo_data_dir


class TestStart:
    def test_basic(self, cmd):
        result, repo_dir = cmd('start')
        assert result.exit_code == 0

        store = config.Store.get_for_repo(repo_dir)
        assert store['running'] is True

        status_file = repo_data_dir(repo_dir) / 'status'
        assert status_file.exists()
        start_timestamp = int(status_file.read_text())
        assert start_timestamp > 0

    def test_dont_restart_already_running_repo(self, cmd):
        result, repo_dir = cmd('start')
        assert result.exit_code == 0

        status_file = repo_data_dir(repo_dir) / 'status'
        assert status_file.exists()
        original_start_timestamp = int(status_file.read_text())
        assert original_start_timestamp > 0

        sleep(2)

        result, repo_dir_new = cmd('start')
        assert result.exit_code == 0
        assert repo_dir == repo_dir_new

        status_file = repo_data_dir(repo_dir) / 'status'
        start_timestamp = int(status_file.read_text())
        assert original_start_timestamp == start_timestamp
