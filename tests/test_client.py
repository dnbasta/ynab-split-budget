from datetime import date
from unittest.mock import patch, MagicMock, ANY

import pytest
from requests import Response

from ynabsplitbudget.client import BaseClient, SyncClient
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction


@pytest.mark.parametrize('budget, account, expected', [('bullshit', 'bullshit', BudgetNotFound),
													   ('sample_budget_id', 'bullshit', AccountNotFound)])
@patch('ynabsplitbudget.client.requests.get')
def test_fetch_account_fails(mock_response, mock_budget, budget, account, expected):
	# Arrange
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = {'data': {'budgets': [mock_budget]}}
	mock_response.return_value = mock_resp_obj

	# Act
	with pytest.raises(expected):
		c = BaseClient(token='', user_name='')
		c.fetch_account(budget_id=budget, account_id=account)


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_account_passes(mock_response, mock_budget):
	# Arrange
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = {'data': {'budgets': [mock_budget]}}
	mock_response.return_value = mock_resp_obj

	# Act
	c = BaseClient(token='', user_name='')
	a = c.fetch_account(budget_id='sample_budget_id', account_id='sample_account_id')

	# Assert
	assert isinstance(a, Account)
	assert a.account_id == 'sample_account_id'
	assert a.budget_id == 'sample_budget_id'
	assert a.account_name == 'sample_account_name'
	assert a.budget_name == 'sample_budget_name'
	assert a.currency == 'sample_iso_code'
	assert a.transfer_payee_id == 'sample_transfer_payee_id'


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_new(mock_response, mock_transaction_dict):
	# Arrange
	mock_resp_obj = MagicMock()
	mock_resp_obj.json.return_value = {'data': {'transactions': [mock_transaction_dict],
												'server_knowledge': 100}}
	mock_response.return_value = mock_resp_obj
	# Act
	c = SyncClient(MagicMock(account=MagicMock(account_id='sample_account')))
	r = c.fetch_roots(since=date(2024,1, 1))

	# Assert
	t = r[0]
	assert isinstance(t, RootTransaction)
	assert t.share_id == '6f66e5aa449e868261ce'
	assert t.account_id == 'sample_account'
	assert t.amount == 1000
	assert t.id == 'sample_id'
	assert t.payee_name == 'sample_payee'
	assert t.memo == 'sample_memo'
	assert t.transaction_date == date(2024, 1, 1)


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_new_empty(mock_response, mock_transaction_dict):
	# Arrange
	mock_resp_obj = MagicMock()
	mock_resp_obj.json.return_value = {'data': {'transactions': [],
												'server_knowledge': 100}}
	mock_response.return_value = mock_resp_obj
	# Act
	c = SyncClient(MagicMock())
	r = c.fetch_roots(since=date(2024, 1, 1))

	# Assert
	assert len(r) == 0


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_balance(mock_response):
	# Arrange
	r = MagicMock()
	r.json.return_value = {'data': {'account': {'cleared_balance': 100}}}
	mock_response.return_value = r
	# Act

	c = SyncClient(user=MagicMock())
	b = c.fetch_balance()

	# Assert
	assert b == 100


@patch('ynabsplitbudget.client.SyncClient._get')
def test_fetch_lookup_no_since(mock_response, mock_transaction_dict):
	# Arrange
	mock_response.return_value = {'transactions': [mock_transaction_dict]}

	# Act
	c = SyncClient(MagicMock())
	r = c.fetch_lookup(since=date(2024, 1, 1))

	assert len(r) == 1
	assert isinstance(r[0], LookupTransaction)


@patch('ynabsplitbudget.client.SyncClient._get')
def test_fetch_lookup_since(mock_get, mock_transaction_dict):
	# Arrange
	mock_get.return_value = {'transactions': [mock_transaction_dict]}

	# Act
	c = SyncClient(MagicMock())
	c.fetch_lookup(since=date(2024, 1, 1))

	mock_get.assert_called_with(ANY, params={'since_date': '2024-01-01'})
