from src.ynab_split_budget.config import Config
from src.ynab_split_budget.repositories.baserepository import BaseRepository
from src.ynab_split_budget.repositories.chargeoperationrepository import ChargeOperationRepository


def test_from_config():
	c = Config.from_path('../')
	br = BaseRepository.from_config(config=c)
	cr = ChargeOperationRepository.from_config(config=c, base_repo=br)
	assert isinstance(cr, ChargeOperationRepository)
