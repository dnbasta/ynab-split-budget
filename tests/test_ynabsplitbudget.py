from io import StringIO
from unittest.mock import patch

import pytest
from yaml.parser import ParserError

from ynabsplitbudget import YnabSplitBudget


def test_from_yaml_file_not_found():

	with pytest.raises(FileNotFoundError):
		YnabSplitBudget.from_yaml(path='/test/path/config.yaml')


@patch('ynabsplitbudget.ynabsplitbudget.Path.open')
def test_user_loader_wrong_file_format(mock_config, mock_config_dict):
	mock_config.return_value = StringIO('{{xxx')

	with pytest.raises(ParserError):
		YnabSplitBudget.from_yaml(path='/test/path/config.yaml')
