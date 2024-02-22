import json
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest
from yaml.parser import ParserError

from ynabsplitbudget.models.exception import UserNotFound, ConfigNotValid
from ynabsplitbudget.models.user import User
from ynabsplitbudget.userloader import UserLoader


@patch('ynabsplitbudget.userloader.Path.open')
def test_user_loader_pass(mock_config, mock_config_dict):
	mock_config.return_value = StringIO(json.dumps(mock_config_dict))

	ul = UserLoader(path='/test/path/config.yaml', user='user_1')

	assert isinstance(ul, UserLoader)


def test_user_loader_file_not_found():
	with pytest.raises(FileNotFoundError):
		ul = UserLoader(path='/test/path/config.yaml', user='user_1')


@patch('ynabsplitbudget.userloader.Path.open')
def test_user_loader_wrong_file_format(mock_config, mock_config_dict):
	mock_config.return_value = StringIO('{{xxx')

	with pytest.raises(ParserError):
		ul = UserLoader(path='/test/path/config.yaml', user='user_1')


@pytest.mark.parametrize('test_input', [{'u1': {}},
										{'u1': {}, 'u2': {}, 'u3': {}},
										{'u1': {}, 'u2': {}}])
@patch('ynabsplitbudget.userloader.Path.open')
def test_user_loader_config_not_valid(mock_path, test_input):
	# Arrange
	mock_path.return_value = StringIO(json.dumps(test_input))

	# Act
	with pytest.raises(ConfigNotValid) as e:
		UserLoader(path='/test/path/config.yaml', user='u1')


@patch('ynabsplitbudget.userloader.Path.open')
def test_user_loader_config_valid(mock_path, mock_config_dict):
	# Arrange
	mock_path.return_value = StringIO(json.dumps(mock_config_dict))

	# Act
	ul = UserLoader(path='/test/path/config.yaml', user='user_1')

	# Assert
	assert isinstance(ul, UserLoader)
	assert ul._config_dict == mock_config_dict


@patch('ynabsplitbudget.userloader.Path.open', return_value=StringIO())
def test_load_fail(mock_path, mock_config_dict):
	# Arrange
	mock_path.return_value = StringIO(json.dumps(mock_config_dict))
	ul = UserLoader(path='/test/path/config.yaml', user='xxx')
	# Act
	with pytest.raises(UserNotFound):
		u = ul.load('xxx')


@patch('ynabsplitbudget.userloader.Path.open', return_value=StringIO())
@patch('ynabsplitbudget.userloader.BaseClient.fetch_account', return_value=MagicMock())
def test_load_pass(mock_account, mock_path, mock_config_dict):
	# Arrange
	mock_path.return_value = StringIO(json.dumps(mock_config_dict))
	ul = UserLoader(path='/test/path/config.yaml', user='user_1')
	# Act
	u = ul.load('user_1')
	# Assert
	assert isinstance(u, User)


@patch('ynabsplitbudget.userloader.Path.open', return_value=StringIO())
@patch('ynabsplitbudget.userloader.BaseClient.fetch_account', return_value=MagicMock())
def test_partner(mock_account, mock_path, mock_config_dict):
	# Arrange
	mock_path.return_value = StringIO(json.dumps(mock_config_dict))

	# Act
	ul = UserLoader(path='/test/path/config', user='user_1')
	p = ul.partner

	# Assert
	assert isinstance(p, User)
	assert p.name == 'user_2'
	assert p.flag == 'red'
	assert p.token == 'token2'


@patch('ynabsplitbudget.userloader.Path.open', return_value=StringIO())
@patch('ynabsplitbudget.userloader.BaseClient.fetch_account', return_value=MagicMock())
def test_user(mock_account, mock_path, mock_config_dict):
	# Arrange
	mock_path.return_value = StringIO(json.dumps(mock_config_dict))

	# Act
	ul = UserLoader(path='/test/path/config', user='user_1')
	u = ul.user

	# Assert
	assert isinstance(u, User)
	assert u.name == 'user_1'
	assert u.flag == 'purple'
	assert u.token == 'token1'
