from src.ynabsplitbudget.config import Config


def test_from_file(conf_path):
	# Act
	c = Config.from_path(path=conf_path)
	# Assert
	assert isinstance(c, Config)
