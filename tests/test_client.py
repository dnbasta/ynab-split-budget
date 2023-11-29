from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from requests import Response

from ynabsplitbudget.client import BaseClient, SyncClient, SplitClient
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.categorysplit import CategorySplit
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.models.flagsplit import FlagSplit
from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.models.transaction import RootTransaction
from ynabsplitbudget.models.user import User
from ynabsplitbudget.ynabsplitbudget import YnabSplitBudget


@pytest.mark.parametrize('budget, account, expected', [('bullshit', 'bullshit', BudgetNotFound),
													   ('sample_budget_name', 'bullshit', AccountNotFound)])
@patch('ynabsplitbudget.client.requests.get')
def test_fetch_account_fails(mock_response, mock_budget, budget, account, expected):
	# Arrange
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = {'data': {'budgets': [mock_budget]}}
	mock_response.return_value = mock_resp_obj

	# Act
	with pytest.raises(expected):
		BaseClient().fetch_account(budget_name=budget, account_name=account, user_name='sample_user',
								   token='sample_token')


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_account_passes(mock_response, mock_budget):
	# Arrange
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = {'data': {'budgets': [mock_budget]}}
	mock_response.return_value = mock_resp_obj

	# Act
	a = BaseClient().fetch_account(budget_name='sample_budget_name',
								   account_name='sample_account_name', user_name='sample_user', token='sample_token')

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
	assert t.amount == 0.01
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

	u = User(name='user_name', flag_splits=[FlagSplit(color='purple', split=0.5)],
			 category_splits=[CategorySplit(name='sample_category_name', split=0.4)],
			 token='sample_token',
			 account=MagicMock())
	c = SplitClient(u)
	st = c.fetch_new_to_split()
	assert isinstance(st[0], SplitTransaction)
	assert st[0].split == 0.5


@patch('ynabsplitbudget.client.requests.get')
def test_fetch_new_to_split_category(mock_response, mock_transaction_dict):
	# Arrange
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = {'data': {'transactions': [mock_transaction_dict]}}
	mock_response.return_value = mock_resp_obj

	u = User(name='user_name', flag_splits=[FlagSplit(color='red', split=0.5)],
			 category_splits=[CategorySplit(name='sample_category_name', split=0.4)],
			 token='sample_token',
			 account=MagicMock())
	c = SplitClient(u)
	st = c.fetch_new_to_split()
	assert isinstance(st[0], SplitTransaction)
	assert st[0].split == 0.4
