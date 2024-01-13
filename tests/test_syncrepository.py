from datetime import date
from unittest.mock import MagicMock, patch

from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction
from ynabsplitbudget.syncrepository import SyncRepository


@patch('ynabsplitbudget.client.SyncClient.fetch_new')
@patch('ynabsplitbudget.client.SyncClient.fetch_lookup')
def test_fetch_new_to_insert_new(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1), id='id')
	mock_changed.return_value = [mock_transaction]
	mock_lookup.return_value = [mock_transaction]
	# Act
	strepo = SyncRepository(user=MagicMock(), partner=MagicMock())
	t = strepo.fetch_new()
	# Assert
	assert isinstance(t[0], RootTransaction)


@patch('ynabsplitbudget.client.SyncClient.fetch_new')
@patch('ynabsplitbudget.client.SyncClient.fetch_lookup')
def test_fetch_new_to_insert_not_new(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1), id='id',
								 share_id='share_id')
	mock_complement = MagicMock(spec=ComplementTransaction, id='id2', share_id='share_id')
	mock_changed.return_value = [mock_transaction]
	mock_lookup.return_value = [mock_complement]
	# Act
	strepo = SyncRepository(user=MagicMock(), partner=MagicMock())
	t = strepo.fetch_new()
	# Assert
	assert len(t) == 0


@patch('ynabsplitbudget.client.SyncClient.fetch_new')
@patch('ynabsplitbudget.client.SyncClient.fetch_lookup')
def test_fetch_new_to_insert_empty(mock_lookup, mock_changed):
	# Arrange
	mock_changed.return_value = []
	mock_lookup.return_value = []
	# Act
	strepo = SyncRepository(user=MagicMock(), partner=MagicMock())
	t = strepo.fetch_new()
	# Assert
	assert len(t) == 0