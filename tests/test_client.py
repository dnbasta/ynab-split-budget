from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from requests import Response

from ynabsplitbudget.client import BaseClient, SyncClient, SplitClient
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound, SplitNotValid
from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.models.transaction import RootTransaction
from ynabsplitbudget.models.user import User
from ynabsplitbudget.transactionbuilder import SplitParser, SplitTransactionBuilder


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
	r = c.fetch_new()

	# Assert
	t = r[0]
	assert isinstance(t, RootTransaction)
	assert t.share_id == '6f66e5aa449e868261ce'
	assert t.account_id == 'sample_account'
	assert t.amount == 1000
	assert t.id == 'sample_id'
	assert t.payee_name == 'sample_payee'
	assert t.memo == 'sample_memo'
	assert t.transaction_date == date(2023, 10, 1)


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_new_empty(mock_response, mock_transaction_dict):
	# Arrange
	mock_resp_obj = MagicMock()
	mock_resp_obj.json.return_value = {'data': {'transactions': [],
												'server_knowledge': 100}}
	mock_response.return_value = mock_resp_obj
	# Act
	c = SyncClient(MagicMock())
	r = c.fetch_new()

	# Assert
	assert len(r) == 0


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_new_to_split_flag(mock_response, mock_transaction_dict):
	# Arrange
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = {'data': {'transactions': [mock_transaction_dict]}}
	mock_response.return_value = mock_resp_obj

	u = User(name='user_name', flag='purple',
			 token='sample_token',
			 account=MagicMock())
	c = SplitClient(u)

	# Act
	st = c.fetch_new_to_split()

	# Assert
	assert isinstance(st[0], SplitTransaction)
	assert st[0].split_amount == 500


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
