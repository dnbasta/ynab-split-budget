from io import StringIO
from unittest.mock import patch

import pytest
from yaml.parser import ParserError

from ynabsplitbudget.fileloader import FileLoader


def test_load_file_not_found():
	with pytest.raises(FileNotFoundError):
		ul = FileLoader(path='/test/path/config.yaml').load()


@patch('ynabsplitbudget.fileloader.Path.open')
def test_user_loader_wrong_file_format(mock_config, mock_config_dict):
	mock_config.return_value = StringIO('{{xxx')

	with pytest.raises(ParserError):
		ul = FileLoader(path='/test/path/config.yaml').load()
