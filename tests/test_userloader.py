import json
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest
from yaml.parser import ParserError

from ynabsplitbudget.models.exception import UserNotFound, ConfigNotValid
from ynabsplitbudget.models.user import User
from ynabsplitbudget.userloader import UserLoader


def test_user_loader_pass(mock_config_dict):
	ul = UserLoader(mock_config_dict)
	assert isinstance(ul, UserLoader)


@pytest.mark.parametrize('test_input', [{'u1': {}},
										{'u1': {}, 'u2': {}, 'u3': {}},
										{'u1': {}, 'u2': {}}])
def test_user_loader_config_not_valid(test_input):

	# Act
	with pytest.raises(ConfigNotValid) as e:
		UserLoader(config_dict=test_input)


def test_user_loader_config_valid(mock_config_dict):
	# Act
	ul = UserLoader(mock_config_dict)

	# Assert
	assert isinstance(ul, UserLoader)
	assert ul._config_dict == mock_config_dict


def test_load_fail(mock_config_dict):
	# Arrange
	ul = UserLoader(mock_config_dict)
	# Act
	with pytest.raises(UserNotFound):
		u = ul.load('xxx')


@patch('ynabsplitbudget.userloader.BaseClient.fetch_account', return_value=MagicMock())
def test_load_pass(mock_account, mock_config_dict):
	# Arrange
	ul = UserLoader(mock_config_dict)
	# Act
	u = ul.load('user_1')
	# Assert
	assert isinstance(u, User)
	assert u.name == 'user_1'
	assert u.flag == 'purple'
	assert u.token == 'token1'


@patch('ynabsplitbudget.userloader.BaseClient.fetch_account', return_value=MagicMock())
def test_partner(mock_account, mock_config_dict):
	# Arrange
	ul = UserLoader(mock_config_dict)

	# Act
	p = ul.load_partner('user_1')

	# Assert
	assert isinstance(p, User)
	assert p.name == 'user_2'
	assert p.flag == 'red'
	assert p.token == 'token2'
