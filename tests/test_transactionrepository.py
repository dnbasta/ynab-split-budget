from datetime import date
from unittest.mock import MagicMock, patch

from ynabsplitaccount.models.transaction import RootTransaction, ComplementTransaction
from ynabsplitaccount.transactionrepository import TransactionRepository


@patch('ynabsplitaccount.client.TransactionClient.fetch_changed')
@patch('ynabsplitaccount.client.TransactionClient.fetch_lookup')
def test_from_config(mock_lookup, mock_changed):
	# Arrange
	mock_transaction = MagicMock(spec=RootTransaction, transaction_date=date(2023, 10, 1))
	mock_changed.return_value = ([mock_transaction], 100)
	mock_lookup.return_value = [mock_transaction]
	# Act
	strepo = TransactionRepository.from_config(MagicMock())

	assert isinstance(strepo.user_1_changed[0], RootTransaction)
	assert isinstance(strepo.user_2_changed[0], RootTransaction)
	assert isinstance(strepo.user_1_lookup[0], RootTransaction)
	assert isinstance(strepo.user_2_lookup[0], RootTransaction)
	assert strepo.user_1_server_knowledge == 100
	assert strepo.user_2_server_knowledge == 100


@patch('ynabsplitaccount.client.TransactionClient.fetch_changed')
@patch('ynabsplitaccount.client.TransactionClient.fetch_lookup')
def test_from_config_empty(mock_lookup, mock_changed):
	# Arrange
	mock_changed.return_value = ([], 100)
	mock_lookup.return_value = []
	# Act
	strepo = TransactionRepository.from_config(MagicMock())

	assert len(strepo.user_1_changed) == 0
	assert len(strepo.user_2_changed) == 0
	assert len(strepo.user_2_lookup) == 0
	assert len(strepo.user_2_lookup) == 0
	assert strepo.user_1_server_knowledge == 100
	assert strepo.user_2_server_knowledge == 100


def test_fetch_new_new():
	# Arrange
	mock_parent = MagicMock(spec=RootTransaction, share_id='x')
	mock_child = MagicMock(spec=ComplementTransaction, share_id='y')
	strepo = TransactionRepository(user_1_changed=[mock_parent],
								   user_2_changed=[],
								   user_1_lookup=[],
								   user_2_lookup=[mock_child],
								   user_1_server_knowledge=100,
								   user_2_server_knowledge=100)

	# Act
	t1 = strepo.fetch_new_user_1()
	t2 = strepo.fetch_new_user_2()
	# Assert
	assert t1[0] == mock_parent
	assert len(t2) == 0


def test_fetch_new_exists():
	# Arrange
	mock_parent = MagicMock(spec=RootTransaction, share_id='x')
	mock_child = MagicMock(spec=ComplementTransaction, share_id='x')
	strepo = TransactionRepository(user_1_changed=[mock_parent],
								   user_2_changed=[],
								   user_1_lookup=[],
								   user_2_lookup=[mock_child],
								   user_1_server_knowledge=100,
								   user_2_server_knowledge=100)

	# Act
	t1 = strepo.fetch_new_user_1()
	t2 = strepo.fetch_new_user_2()

	# Assert
	assert len(t1) == 0
	assert len(t2) == 0
