from src.ynab_split_budget.repositories.baserepository import BaseRepository
from src.ynab_split_budget.config import Config


def test_from_config(conf_path):
	c = Config.from_path(path=conf_path)
	br = BaseRepository.from_config(config=c)
	assert isinstance(br, BaseRepository)
