import pytest
import os


@pytest.fixture
def conf_path():
	return f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/'
