from datetime import date
from unittest.mock import MagicMock, patch

from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction
from ynabsplitbudget.syncrepository import SyncRepository


@patch('ynabsplitbudget.client.Client.fetch_roots')
@patch('ynabsplitbudget.client.Client.fetch_lookup')
def test_fetch_new_to_insert_new(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1), id='id',
								 share_id='share_id')
	mock_lookup_transaction = MagicMock(spec=RootTransaction, share_id='share_id2')
	mock_changed.return_value = [mock_transaction]
	mock_lookup.return_value = [mock_lookup_transaction]
	# Act
	strepo = SyncRepository(user=MagicMock(), partner=MagicMock())
	t = strepo.fetch_roots_wo_complement(since=date(2024, 1, 1))
	# Assert
	assert isinstance(t[0], RootTransaction)


@patch('ynabsplitbudget.client.Client.fetch_roots')
@patch('ynabsplitbudget.client.Client.fetch_lookup')
def test_fetch_new_to_insert_not_new(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1), id='id',
								 share_id='share_id')
	mock_complement = MagicMock(spec=ComplementTransaction, id='id2', share_id='share_id')
	mock_changed.return_value = [mock_transaction]
	mock_lookup.return_value = [mock_complement]
	# Act
	strepo = SyncRepository(user=MagicMock(), partner=MagicMock())
	t = strepo.fetch_roots_wo_complement(since=date(2024, 1, 1))
	# Assert
	assert len(t) == 0


@patch('ynabsplitbudget.client.Client.fetch_roots')
@patch('ynabsplitbudget.client.Client.fetch_lookup')
def test_fetch_new_to_insert_empty(mock_lookup, mock_changed):
	# Arrange
	mock_changed.return_value = []
	mock_lookup.return_value = []
	# Act
	strepo = SyncRepository(user=MagicMock(), partner=MagicMock())
	t = strepo.fetch_roots_wo_complement(since=date(2024, 1, 1))
	# Assert
	assert len(t) == 0
