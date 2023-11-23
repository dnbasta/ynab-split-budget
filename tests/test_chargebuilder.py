from typing import get_type_hints
from unittest.mock import MagicMock
import pytest

from src.ynabsplitbudget.builders.chargebuilder import ChargeBuilder
from src.ynabsplitbudget.models.user import User
from src.ynabsplitbudget.models.charge import ChargeNew, ChargeNewIncompleteOwner, ChargeNewIncompleteRecipient, ChargeRecipientDeleted, ChargeChanged, ChargeOwnerDeleted
from src.ynabsplitbudget.models.transaction import TransactionPaidToSplit, TransactionOwed, TransactionPaidTransfer, TransactionReference, TransactionPaidSplit, TransactionPaidDeleted
from src.ynabsplitbudget.repositories.transactionlookuprepository import TransactionLookupRepository

MOCK_OWED = MagicMock(spec=TransactionOwed(**get_type_hints(TransactionOwed)))
MOCK_OWED.owed = 5
MOCK_OWED.deleted = False

MOCK_OWED_DELETED = MagicMock(spec=TransactionOwed(**get_type_hints(TransactionOwed)))
MOCK_OWED_DELETED.deleted = True

MOCK_REFERENCE = MagicMock(spec=TransactionReference(**get_type_hints(TransactionReference)))


@pytest.mark.parametrize('transaction, owed, lookup, expected', [
	(TransactionPaidToSplit, 5, None, ChargeNew),
	(TransactionPaidToSplit, 5, MOCK_OWED_DELETED, ChargeNew),
	(TransactionPaidToSplit, 5, MOCK_OWED, ChargeNewIncompleteOwner),
	(TransactionPaidToSplit, 6, MOCK_OWED_DELETED, ChargeNew),
	(TransactionPaidToSplit, 6, MOCK_OWED, ChargeNewIncompleteOwner),

	(TransactionPaidTransfer, 5, None, ChargeNewIncompleteRecipient),
	(TransactionPaidTransfer, 5, MOCK_OWED, type(None)),
	(TransactionPaidTransfer, 5, MOCK_OWED_DELETED, ChargeRecipientDeleted),
	(TransactionPaidTransfer, 6, MOCK_OWED, ChargeChanged),
	(TransactionPaidTransfer, 6, MOCK_OWED_DELETED, ChargeRecipientDeleted),

	(TransactionPaidSplit, 5, None, ChargeNewIncompleteRecipient),
	(TransactionPaidSplit, 5, MOCK_OWED_DELETED, ChargeRecipientDeleted),
	(TransactionPaidSplit, 5, MOCK_OWED, type(None)),
	(TransactionPaidSplit, 6, MOCK_OWED_DELETED, ChargeRecipientDeleted),
	(TransactionPaidSplit, 6, MOCK_OWED, ChargeChanged),

	(TransactionPaidDeleted, 5, None, type(None)),
	(TransactionPaidDeleted, 5, MOCK_OWED, ChargeOwnerDeleted),
	(TransactionPaidDeleted, 5, MOCK_OWED_DELETED, type(None)),
	(TransactionPaidDeleted, 6, MOCK_OWED, ChargeOwnerDeleted),
	(TransactionPaidDeleted, 6, MOCK_OWED_DELETED, type(None)),
])
def test_from_owner_transaction(transaction, owed, lookup, expected):
	# Arrange
	ul1 = MagicMock(spec=TransactionLookupRepository)
	ul1.fetch_recipient_by_hashed_id.return_value = lookup
	cb = ChargeBuilder(user_2_lookup=ul1,
					   user_1_lookup=ul1,
					   user_1=MagicMock(spec=User),
					   user_2=MagicMock(spec=User))
	t = MagicMock(spec=transaction(**get_type_hints(transaction)))
	t.paid = 10
	t.owed = owed

	# Act
	c = cb.from_owner_transaction(t)

	# Assert
	assert isinstance(c, expected)
