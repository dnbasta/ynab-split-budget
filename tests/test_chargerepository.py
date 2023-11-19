from src.ynabsplitbudget.config import Config
from src.ynabsplitbudget.repositories.baserepository import BaseRepository
from src.ynabsplitbudget.repositories.chargeoperationrepository import ChargeOperationRepository


def test_from_config(conf_path):
	c = Config.from_path(path=conf_path)
	br = BaseRepository.from_config(config=c)
	cr = ChargeOperationRepository.from_config(config=c, base_repo=br)
	assert isinstance(cr, ChargeOperationRepository)
