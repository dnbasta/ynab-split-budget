from datetime import date, datetime
from unittest.mock import MagicMock, ANY

import pytest
from requests import Response, HTTPError

from ynabsplitbudget.client import Client
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction, ComplementTransaction


@pytest.fixture
def mock_client():
    client = Client(token='', user_name='', budget_id='', account_id='account_id')
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


def test_fetch_new_cleared_only(mock_client, mock_transaction_dict):
    # Arrange
    mock_transaction_uncleared = mock_transaction_dict.copy()
    mock_transaction_uncleared['cleared'] = 'uncleared'
    mock_client.session.get.return_value = mock_response({'data': {'transactions': [mock_transaction_dict,
                                                                                    mock_transaction_uncleared],
                                                                   'server_knowledge': 100}})
    # Act
    r = mock_client.fetch_roots(since=date(2024, 1, 1), include_uncleared=False)

    # Assert
    assert len(r) == 1
    t = r[0]
    assert isinstance(t, RootTransaction)
    assert t.share_id == '6f66e5aa449e868261ce'
    assert t.account_id == 'sample_account'
    assert t.amount == 1000
    assert t.id == 'sample_id'
    assert t.payee_name == 'sample_payee'
    assert t.memo == 'sample_memo'
    assert t.transaction_date == date(2024, 1, 1)


def test_fetch_new(mock_client, mock_transaction_dict):
    # Arrange
    mock_transaction_dict['cleared'] = 'uncleared'
    mock_client.session.get.return_value = mock_response({'data': {'transactions': [mock_transaction_dict],
                                                                   'server_knowledge': 100}})
    # Act
    r = mock_client.fetch_roots(since=date(2024, 1, 1), include_uncleared=True)

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
    r = mock_client.fetch_roots(since=date(2024, 1, 1), include_uncleared=False)

    # Assert
    assert len(r) == 0


def test_fetch_balance(mock_client):
    # Arrange
    mock_client.session.get.return_value = mock_response({'data': {'account': {'balance': 100}}})
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


def test_insert_complement(mock_client, mock_transaction_dict):
    # Arrange
    mock_root = RootTransaction(id='id', share_id='share_id', account_id='account_id_o',
                    transaction_date=date(2024, 1, 1), memo='memo', payee_name='payee_name', amount=1000)
    mock_transaction_dict['import_id'] = 's||xxx'
    mock_client.session.post.return_value = mock_response({'data': {'transactions': [mock_transaction_dict],
                                                                    'duplicate_import_ids': []}})

    # Act
    c = mock_client.insert_complements([mock_root])

    # Assert
    mock_client.session.post.assert_called_once()
    post_dict = mock_client.session.post.call_args_list[0][1]['json']['transactions'][0]
    assert post_dict['account_id'] == mock_client.account_id
    assert post_dict['date'] == datetime.strftime(mock_root.transaction_date, '%Y-%m-%d')
    assert post_dict['amount'] == - mock_root.amount
    assert post_dict['payee_name'] == mock_root.payee_name
    assert post_dict['memo'] == mock_root.memo
    assert post_dict['import_id'] == f's||{mock_root.share_id}||0'

    assert isinstance(c[0], ComplementTransaction)


def test_insert_complement_iteration(mock_client, mock_transaction_dict):
    # Arrange
    mock_root = RootTransaction(id='id', share_id='share_id', account_id='account_id_o',
                    transaction_date=date(2024, 1, 1), memo='memo', payee_name='payee_name', amount=1000)
    mock_transaction_dict['import_id'] = 's||xxx|2'
    mock_client.session.post.side_effect = [mock_response({'data': {'transactions': [],
                                                                    'duplicate_import_ids': [f's||{mock_root.share_id}||1']}}),
                                                mock_response({'data': {'transactions': [mock_transaction_dict],
                                                                        'duplicate_import_ids': []}})]

    # Act
    c = mock_client.insert_complements([mock_root])

    # Assert
    assert mock_client.session.post.call_count == 2
    mock_client.session.post.assert_called_with(ANY, json=dict(transactions=[{'account_id': 'account_id',
                                                                              'date': '2024-01-01',
                                                                              'amount': -1000,
                                                                              'payee_name': 'payee_name',
                                                                              'memo': 'memo',
                                                                              'cleared': 'cleared',
                                                                              'approved': False,
                                                                              'import_id': 's||share_id||2'}]))
    post_dict = mock_client.session.post.call_args_list[1][1]['json']['transactions'][0]
    assert post_dict['import_id'] == f's||{mock_root.share_id}||2'
