from unittest.mock import patch, MagicMock

from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.transactionbuilder import SplitTransactionBuilder


@patch('ynabsplitbudget.client.SplitTransaction.from_dict', return_value=MagicMock(spec=SplitTransaction))
def test_build_transaction_success(mock):
	# Arrange
	c = SplitTransactionBuilder()
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': 1000, 'memo': 'xxx'}

	# Act
	st = c.build(t_dict=t_dict)

	# Assert
	mock.assert_called_once_with(t_dict=t_dict, split_amount=500)


@patch('ynabsplitbudget.client.SplitTransaction.from_dict', return_value=MagicMock(spec=SplitTransaction))
def test_build_transaction_fail(mock, caplog):
	# Arrange
	c = SplitTransactionBuilder()
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': 1000, 'memo': '@110%'}

	# Act
	with caplog.at_level('ERROR'):
		st = c.build(t_dict=t_dict)
		assert len(caplog.records) == 1
		assert caplog.records[0].levelname == 'ERROR'
		assert len(caplog.records[0].message) > 0

	# Assert
	assert not mock.called
	assert st is None
