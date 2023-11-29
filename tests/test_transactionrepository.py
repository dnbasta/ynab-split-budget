from datetime import date
from unittest.mock import MagicMock, patch

from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction
from ynabsplitbudget.transactionrepository import TransactionRepository


@patch('ynabsplitbudget.client.TransactionClient.fetch_changed')
@patch('ynabsplitbudget.client.TransactionClient.fetch_lookup')
def test_populate_new(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1), id='id')
	mock_changed.return_value = [mock_transaction]
	mock_lookup.return_value = [mock_transaction]
	# Act
	strepo = TransactionRepository(MagicMock()).populate()

	assert isinstance(strepo.user_1[0], RootTransaction)
	assert isinstance(strepo.user_2[0], RootTransaction)


@patch('ynabsplitbudget.client.TransactionClient.fetch_changed')
@patch('ynabsplitbudget.client.TransactionClient.fetch_lookup')
def test_populate_not_new(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1), id='id',
								 share_id='share_id')
	mock_complement = MagicMock(spec=ComplementTransaction, id='id2', share_id='share_id')
	mock_changed.return_value = [mock_transaction]
	mock_lookup.return_value = [mock_complement]
	# Act
	strepo = TransactionRepository(MagicMock()).populate()

	assert len(strepo.user_1) == 0


@patch('ynabsplitbudget.client.TransactionClient.fetch_changed')
@patch('ynabsplitbudget.client.TransactionClient.fetch_lookup')
def test_populate_empty(mock_lookup, mock_changed):
	# Arrange
	mock_changed.return_value = []
	mock_lookup.return_value = []
	# Act
	strepo = TransactionRepository(MagicMock()).populate()

	assert len(strepo.user_1) == 0
	assert len(strepo.user_2) == 0