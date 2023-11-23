from src.ynabsplitbudget.repositories.baserepository import BaseRepository
from src.ynabsplitbudget.repositories.chargeoperationrepository import ChargeOperationRepository


def test_from_config(prod_conf):
	br = BaseRepository.from_config(config=prod_conf)
	cr = ChargeOperationRepository.from_config(config=prod_conf, base_repo=br)
	assert isinstance(cr, ChargeOperationRepository)
