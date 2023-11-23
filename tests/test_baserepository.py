from src.ynabsplitbudget.repositories.baserepository import BaseRepository


def test_from_config(prod_conf):
	br = BaseRepository.from_config(config=prod_conf)
	assert isinstance(br, BaseRepository)
