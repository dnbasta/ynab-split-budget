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
	assert t.amount == 1
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
	assert st[0].split_amount == 0.5


@pytest.mark.parametrize('test_input, expected', [('xxx', 1), ('xxx @25%:xxx', 0.5), ('@33%', 0.66), ('@0.7', 0.7),
												  (None, 1)])
def test__parse_split_pass(test_input, expected):
	# Arrange
	c = SplitClient(user=MagicMock())
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': 2000, 'memo': test_input}

	# Act
	split_amount = c._parse_split(t_dict)

	# Assert
	assert split_amount == expected


@pytest.mark.parametrize('test_input', ['@110%', '@2'])
def test__parse_split_fail(test_input):
	# Arrange
	c = SplitClient(user=MagicMock())
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': 1000, 'memo': test_input}

	# Assert
	with pytest.raises(SplitNotValid):
		# Act
		c._parse_split(t_dict)


@patch('ynabsplitbudget.client.SplitTransaction.from_dict', return_value=MagicMock(spec=SplitTransaction))
def test__build_transaction_success(mock):
	# Arrange
	c = SplitClient(user=MagicMock())
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': 1000, 'memo': 'xxx'}

	# Act
	st = c._build_transaction(t_dict=t_dict)

	# Assert
	mock.assert_called_once_with(t_dict=t_dict, split_amount=0.5)


@patch('ynabsplitbudget.client.SplitTransaction.from_dict', return_value=MagicMock(spec=SplitTransaction))
def test__build_transaction_fail(mock):
	# Arrange
	c = SplitClient(user=MagicMock())
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': 1000, 'memo': '@110%'}

	# Act
	st = c._build_transaction(t_dict=t_dict)

	# Assert
	assert not mock.called
	assert st is None
