import json
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest
from yaml.parser import ParserError

from ynabsplitbudget.models.exception import UserNotFound
from ynabsplitbudget.models.user import User
from ynabsplitbudget.ynabsplitbudget import UserLoader


@patch('ynabsplitbudget.ynabsplitbudget.Path.open')
def test_user_loader_pass(mock_config, mock_config_dict):
	mock_config.return_value = StringIO(json.dumps(mock_config_dict))

	ul = UserLoader(path='/test/path/config.yaml')

	assert isinstance(ul, UserLoader)


def test_user_loader_fail():

	with pytest.raises(FileNotFoundError):
		ul = UserLoader(path='/test/path/config.yaml')


@patch('ynabsplitbudget.ynabsplitbudget.Path.open')
def test_user_loader_fail_format(mock_config, mock_config_dict):
	mock_config.return_value = StringIO('{{xxx')

	with pytest.raises(ParserError):
		ul = UserLoader(path='/test/path/config.yaml')


@patch('ynabsplitbudget.ynabsplitbudget.Path.open', return_value=StringIO())
def test_load_fail(mock_path, mock_config_dict):
	# Arrange
	ul = UserLoader(path='/test/path/config.yaml')
	ul._config_dict = mock_config_dict
	# Act
	with pytest.raises(UserNotFound):
		u = ul.load('user')


@patch('ynabsplitbudget.ynabsplitbudget.Path.open', return_value=StringIO())
@patch('ynabsplitbudget.ynabsplitbudget.BaseClient.fetch_account', return_value=MagicMock())
def test_load_pass(mock_account, mock_path, mock_config_dict):
	# Arrange
	ul = UserLoader(path='/test/path/config.yaml')
	ul._config_dict = mock_config_dict
	# Act
	u = ul.load('user_1')
	# Assert
	assert isinstance(u, User)

