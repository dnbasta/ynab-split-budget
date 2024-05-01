from io import StringIO
from unittest.mock import patch

import pytest
from yaml.parser import ParserError

from ynabsplitbudget import User


def test_from_yaml_file_not_found():

	with pytest.raises(FileNotFoundError):
		User.from_yaml(path='/test/path/config.yaml')


@patch('ynabsplitbudget.models.user.Path.open')
def test_user_loader_wrong_file_format(mock_config, mock_config_dict):
	mock_config.return_value = StringIO('{{xxx')

	with pytest.raises(ParserError):
		User.from_yaml(path='/test/path/config.yaml')
