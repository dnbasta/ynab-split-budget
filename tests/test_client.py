from datetime import date
from unittest.mock import MagicMock, ANY

import pytest
from requests import Response

from ynabsplitbudget.client import Client
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction


@pytest.fixture
def mock_client():
	client = Client(token='', user_name='', budget_id='', account_id='')
	client.session = MagicMock()
	return client


def mock_response(data: dict) -> MagicMock:
	mock_resp_obj = MagicMock(spec=Response)
	mock_resp_obj.json.return_value = data
	return mock_resp_obj


@pytest.mark.parametrize('budget, account, expected', [('bullshit', 'bullshit', BudgetNotFound),
													   ('sample_budget_id', 'bullshit', AccountNotFound)])
def test_fetch_account_fails(mock_client, mock_budget, budget, account, expected):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'budgets': [mock_budget]}})

	# Act
	with pytest.raises(expected):
		mock_client.fetch_account(budget_id=budget, account_id=account)


def test_fetch_account_passes(mock_client, mock_budget):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'budgets': [mock_budget]}})

	# Act
	a = mock_client.fetch_account(budget_id='sample_budget_id', account_id='sample_account_id')

	# Assert
	assert isinstance(a, Account)
	assert a.account_id == 'sample_account_id'
	assert a.budget_id == 'sample_budget_id'
	assert a.account_name == 'sample_account_name'
	assert a.budget_name == 'sample_budget_name'
	assert a.currency == 'sample_iso_code'
	assert a.transfer_payee_id == 'sample_transfer_payee_id'


def test_fetch_new(mock_client, mock_transaction_dict):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'transactions': [mock_transaction_dict],
												'server_knowledge': 100}})
	# Act
	r = mock_client.fetch_roots(since=date(2024,1, 1))

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


def test_fetch_new_empty(mock_client, mock_transaction_dict):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'transactions': [],
												'server_knowledge': 100}})
	# Act
	r = mock_client.fetch_roots(since=date(2024, 1, 1))

	# Assert
	assert len(r) == 0


def test_fetch_balance(mock_client):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'account': {'cleared_balance': 100}}})
	# Act
	b = mock_client.fetch_balance()

	# Assert
	assert b == 100


def test_fetch_lookup_no_since(mock_client, mock_transaction_dict):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'transactions': [mock_transaction_dict]}})

	# Act
	r = mock_client.fetch_lookup(since=date(2024, 1, 1))

	assert len(r) == 1
	assert isinstance(r[0], LookupTransaction)


def test_fetch_lookup_since(mock_client, mock_transaction_dict):
	# Arrange
	mock_client.session.get.return_value = mock_response({'data': {'transactions': [mock_transaction_dict]}})

	# Act
	mock_client.fetch_lookup(since=date(2024, 1, 1))

	mock_client.session.get.assert_called_with(ANY, params={'since_date': '2024-01-01'})
