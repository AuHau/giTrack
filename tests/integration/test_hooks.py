from unittest import mock

from .helpers import ProviderForTesting


class TestHooks:

    def test_basic(self, cmd, mocker, commit):
        result, _ = cmd('start', git_inited=True)
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')
        mocker.spy(ProviderForTesting, 'start')

        commit('Some message')
        result, _ = cmd('hooks post-commit')
        assert result.exit_code == 0

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, 'Some message', force=False, project=None, task=None)
        ProviderForTesting.start.assert_called_once_with(mock.ANY)

    def test_ignored_non_running_repos(self, cmd, mocker, commit):
        result, _ = cmd('init --no-hook', inited=False, git_inited=True)
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')
        mocker.spy(ProviderForTesting, 'start')

        commit('Some message')
        result, _ = cmd('hooks post-commit')
        assert result.exit_code == 0

        assert ProviderForTesting.stop.call_count == 0
        assert ProviderForTesting.start.call_count == 0

    def test_task_static(self, cmd, mocker, commit):
        result, _ = cmd('start', git_inited=True)
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')
        mocker.spy(ProviderForTesting, 'start')

        commit('Some message')
        result, _ = cmd('hooks post-commit', config='task_static.config')
        assert result.exit_code == 0

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, 'Some message', force=False, project=None, task='some task name')
        ProviderForTesting.start.assert_called_once_with(mock.ANY)

    def test_task_dynamic_branch(self, cmd, mocker, commit):
        result, _ = cmd('start', git_inited=True)
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')
        mocker.spy(ProviderForTesting, 'start')

        commit('Some message', branch='#123_Some_brunch')
        result, _ = cmd('hooks post-commit', config='task_dynamic_branch.config')
        assert result.exit_code == 0

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, 'Some message', force=False, project=None, task=123)
        ProviderForTesting.start.assert_called_once_with(mock.ANY)

    def test_task_dynamic_commit(self, cmd, mocker, commit):
        result, _ = cmd('start', git_inited=True)
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')
        mocker.spy(ProviderForTesting, 'start')

        commit('#321 Some message')
        result, _ = cmd('hooks post-commit', config='task_dynamic_commit.config')
        assert result.exit_code == 0

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, '#321 Some message', force=False, project=None, task=321)
        ProviderForTesting.start.assert_called_once_with(mock.ANY)

    def test_project(self, cmd, mocker, commit):
        result, _ = cmd('start', git_inited=True)
        assert result.exit_code == 0

        mocker.spy(ProviderForTesting, 'stop')
        mocker.spy(ProviderForTesting, 'start')

        commit('Some message')
        result, _ = cmd('hooks post-commit', config='project.config')
        assert result.exit_code == 0

        ProviderForTesting.stop.assert_called_once_with(mock.ANY, 'Some message', force=False, project=123, task=None)
        ProviderForTesting.start.assert_called_once_with(mock.ANY)
