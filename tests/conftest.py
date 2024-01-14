import pytest


@pytest.fixture
def mock_transaction_dict():
	return {'id': 'sample_id',
			'memo': 'sample_memo',
			'payee_name': 'sample_payee',
			'payee_id': 'sample_payee_id',
			'category_name': 'sample_category_name',
			'category_id': 'sample_category_id',
			'deleted': False,
			'account_id': 'sample_account',
			'amount': 1000,
			'date': '2023-10-01',
			'cleared': 'cleared',
			'import_id': None,
			'flag_color': 'purple',
			'subtransactions': []}


@pytest.fixture
def mock_budget():
	return {'id': 'sample_budget_id',
			'name': 'sample_budget_name',
			'currency_format': {'iso_code': 'sample_iso_code'},
			'accounts': [{'id': 'sample_account_id',
						  'name': 'sample_account_name',
						  'deleted': False,
						  'transfer_payee_id': 'sample_transfer_payee_id'}]
			}


@pytest.fixture
def mock_config_dict():
	return {'user_1': {
				'token': 'token1',
				'account': 'account1',
				'budget': 'budget1',
				'flag': 'purple',
			},
			'user_2': {
				'token': 'token2',
				'account': 'account2',
				'budget': 'budget2',
				'flag': 'red'
			}
		}
