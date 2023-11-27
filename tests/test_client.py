from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from requests import Response

from ynabsplitaccount.client import BaseClient, ShareTransactionClient
from ynabsplitaccount.models.account import BaseAccount
from ynabsplitaccount.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitaccount.models.sharetransaction import ShareTransactionParent, ShareTransactionChild


@pytest.mark.parametrize('budget, account, expected', [('bullshit', 'bullshit', BudgetNotFound),
											 ('sample_budget_name', 'bullshit', AccountNotFound)])
def test_fetch_account_fails(mock_budget, budget, account, expected):
	# Arrange
	mock_response = MagicMock(spec=Response)
	mock_response.json.return_value = {'data': {'budgets': [mock_budget]}}

	# Act
	with patch('ynabsplitaccount.client.requests.get', return_value=mock_response):
		with pytest.raises(expected) as e:
			BaseClient().fetch_account(budget_name=budget, account_name=account, user_name='sample_user',
									   token='sample_token')


def test_fetch_account_passes(mock_budget):
	# Arrange
	mock_response = MagicMock(spec=Response)
	mock_response.json.return_value = {'data': {'budgets': [mock_budget]}}

	# Act
	with patch('ynabsplitaccount.client.requests.get', return_value=mock_response):
		a = BaseClient().fetch_account(budget_name='sample_budget_name',
								 account_name='sample_account_name', user_name='sample_user', token='sample_token')

	# Assert
	assert isinstance(a, BaseAccount)
	assert a.account_id == 'sample_account_id'
	assert a.budget_id == 'sample_budget_id'
	assert a.account_name == 'sample_account_name'
	assert a.budget_name == 'sample_budget_name'
	assert a.currency == 'sample_iso_code'
	assert a.transfer_payee_id == 'sample_transfer_payee_id'


def test_fetch_share_transactions_parent(mock_transaction_dict):
	# Arrange
	mock_response = MagicMock(spec=Response)
	mock_response.json.return_value = {'data': {'transactions': [mock_transaction_dict],
												'server_knowledge': 100}}
	# Act
	with patch('ynabsplitaccount.client.requests.get', return_value=mock_response):
		c = ShareTransactionClient(MagicMock())
		r = c.fetch_changed()

	# Assert
	t = r[0][0]
	assert isinstance(t, ShareTransactionParent)
	assert t.share_id == '6f66e5aa449e868261ce'
	assert t.account_id == 'sample_account'
	assert t.amount == -0.01
	assert t.id == 'sample_id'
	assert t.payee_name == 'sample_payee'
	assert t.memo == 'sample_memo'
	assert t.transaction_date == date(2023, 10, 1)


def test_fetch_share_transactions_empty(mock_transaction_dict):
	# Arrange
	mock_response = MagicMock(spec=Response)
	mock_response.json.return_value = {'data': {'transactions': [],
												'server_knowledge': 100}}
	# Act
	with patch('ynabsplitaccount.client.requests.get', return_value=mock_response):
		c = ShareTransactionClient(MagicMock())
		r = c.fetch_changed()

	# Assert
	assert len(r[0]) == 0
