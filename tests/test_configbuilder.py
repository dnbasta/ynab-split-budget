from src.ynabsplitbudget.builders.configbuilder import ConfigBuilder
from src.ynabsplitbudget.models.config import Config
from tests.conftest import mock_dataclass


def test_build_from_path(prod_conf_path):
	c = ConfigBuilder(path=prod_conf_path).build_from_path()
	assert isinstance(c, Config)


def test_build_from_config(prod_conf_path):
	cb = ConfigBuilder(path=prod_conf_path)
	c = mock_dataclass(Config)
	cn = cb.build_from_config(c, user_1_server_knowledge=0, user_2_server_knowledge=0)
	assert isinstance(cn, Config)
	assert cn.user_1.account.server_knowledge == 0
	assert cn.user_2.account.server_knowledge == 0
