from src.ynabsplitbudget.repositories.baserepository import BaseRepository
from src.ynabsplitbudget.config import Config


def test_from_config(prod_conf):
	c = Config.from_path(path=prod_conf)
	br = BaseRepository.from_config(config=c)
	assert isinstance(br, BaseRepository)
