import json
from io import StringIO
from unittest.mock import patch, MagicMock

from ynabsplitbudget.ynabsplitbudget import YnabSplitBudget


@patch('ynabsplitbudget.ynabsplitbudget.BaseClient.fetch_account')
@patch('ynabsplitbudget.ynabsplitbudget.Path.open')
def test_ynab_share_account(mock_config, mock_account):
	mock_config_dict = {'user_1': {
						'name': 'name1',
						'token': 'token1',
						'account': 'account1',
						'budget': 'budget1'},
					'user_2': {
						'name': 'name2',
						'token': 'token2',
						'account': 'account2',
						'budget': 'budget2'}
					}
	mock_config.return_value = StringIO(json.dumps(mock_config_dict))
	mock_account.return_value = MagicMock()

	# Act
	ysa = YnabSplitBudget(path='/test/path/config.yaml')

	# Assert
	assert ysa._config.user_1.name == 'name1'
	assert ysa._config.user_1.token == 'token1'
	mock_account.assert_any_call(user_name='name1', account_name='account1', budget_name='budget1', token='token1')
	assert ysa._config.user_2.name == 'name2'
	assert ysa._config.user_2.token == 'token2'
	mock_account.assert_any_call(budget_name='budget2', account_name='account2', user_name='name2', token='token2')