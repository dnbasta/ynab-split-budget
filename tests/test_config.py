from src.ynab_split_budget.config import Config


def test_from_file():
	# Act
	c = Config.from_path(path='../')
	# Assert
	assert isinstance(c, Config)
