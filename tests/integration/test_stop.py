from unittest import mock

from .helpers import repo_data_dir, ProviderForTesting


class TestStop:
    def test_basic(self, cmd, mocker):
        result, repo_dir = cmd('start')
        assert result.exit_code == 0

        status_file = repo_data_dir(repo_dir) / 'status'
        assert status_file.exists()
        original_start_timestamp = int(status_file.read_text())
        assert original_start_timestamp > 0

        mocker.spy(ProviderForTesting, 'stop')

        result, repo_dir = cmd('stop')
        assert result.exit_code == 0

        status_file = repo_data_dir(repo_dir) / 'status'
        assert status_file.exists()
        assert status_file.read_text() == ""

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, None)

    def test_description(self, cmd, mocker):
        result, repo_dir = cmd('start')
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')

        result, _ = cmd('stop --description \'Some description\'')
        assert result.exit_code == 0

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, 'Some description')

    def test_ignore_non_running_repos(self, cmd, mocker):
        mocker.spy(ProviderForTesting, 'stop')

        result, _ = cmd('stop')
        assert result.exit_code == 0

        assert ProviderForTesting.stop.call_count == 0

    def test_cancel(self, cmd, mocker):
        result, repo_dir = cmd('start')
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'cancel')

        result, _ = cmd('stop --cancel')
        assert result.exit_code == 0

        assert ProviderForTesting.cancel.call_count == 1
