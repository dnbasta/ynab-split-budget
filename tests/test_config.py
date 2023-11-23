import yaml

from src.ynabsplitbudget.models.config import Config
from tests.conftest import create_mock_object


def test_save(tmp_path):
	# Arrange
	test_path = f'{tmp_path}/config.yaml'
	config = create_mock_object(Config, {'path': test_path})

	# Act
	config.save()

	# Assert
	with open(test_path, 'r') as f:
		t_dict = yaml.safe_load(f)

	for u in ['user_1', 'user_2']:
		for k in ['name', 'token']:
			assert t_dict[u][k] == getattr(getattr(config, u), k)

		for k1, k2 in [('account', 'account_name'), ('budget', 'budget_name')]:
			assert t_dict[u][k1] == getattr(getattr(config, u).account, k2)
