import pytest


@pytest.fixture
def mock_transaction_dict():
	return {'id': 'sample_id',
			'memo': 'sample_memo',
			'payee_name': 'sample_payee',
			'deleted': False,
			'account_id': 'sample_account',
			'amount': 10,
			'date': '2023-10-01',
			'cleared': 'cleared',
			'import_id': None}


@pytest.fixture
def mock_budget():
	return {'id': 'sample_budget_id',
			'name': 'sample_budget_name',
			'currency_format': {'iso_code': 'sample_iso_code'},
			'accounts': [{'id': 'sample_account_id',
			   		      'name': 'sample_account_name',
						  'deleted': False,
						  'transfer_payee_id': 'sample_transfer_payee_id'}],
															 }