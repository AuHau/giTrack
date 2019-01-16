from pathlib import Path

import pytest
from pytest_mock import MockFixture

# @pytest.fixture(scope="session", autouse=True)
# def set_default_config(pytestconfig):
#     mocker = MockFixture(pytestconfig)
#
#     mocker.patch.object(config.IniConfigMixin, 'DEFAULT_CONFIG_PATH')
#     config.IniConfigMixin.DEFAULT_CONFIG_PATH.return_value = str(Path(__file__) / 'configs' / 'default.config')
#
#     yield
#     mocker.stopall()
