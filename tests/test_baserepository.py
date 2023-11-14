from src.ynab_split_budget.repositories.baserepository import BaseRepository
from src.ynab_split_budget.config import Config


def test_from_config():
	c = Config.from_path(path='../')
	br = BaseRepository.from_config(config=c)
	assert isinstance(br, BaseRepository)
