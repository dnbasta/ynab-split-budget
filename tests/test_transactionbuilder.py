from unittest.mock import MagicMock

import pytest

from ynabsplitbudget.models.transaction import ComplementTransaction
from ynabsplitbudget.transactionbuilder import TransactionBuilder


@pytest.mark.parametrize('test_input, expected', [('s||xxx||1', 1), ('s||xxx', 0)] )
def test_build_complement_import_ids(test_input, expected, mock_transaction_dict):
	# Arrange
	tb = TransactionBuilder(account_id='')
	mock_transaction_dict['import_id'] = test_input

	# Act
	t = tb.build_complement(mock_transaction_dict)

	# Assert
	assert isinstance(t, ComplementTransaction)
	assert t.iteration == expected
