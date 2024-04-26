from unittest.mock import MagicMock, PropertyMock

from ynabtransactionadjuster.models import Category

from ynabsplitbudget.adjusters import ReconcileAdjuster


def test_filter():

	ra = ReconcileAdjuster(payees=MagicMock(), categories=MagicMock(), credentials=MagicMock(), transactions=MagicMock())
	# Act
	t = ra.filter([PropertyMock(cleared='cleared'), PropertyMock(cleared='uncleared'), PropertyMock(cleared='reconciled')])
	assert len(t) == 1


def test_adjust():
	# Arrange
	ma = ReconcileAdjuster(payees=MagicMock(), categories=MagicMock(), credentials=MagicMock(), transactions=MagicMock())
	ma.categories.fetch_by_name.return_value = MagicMock(spec=Category)
	t = ma.adjust(PropertyMock(cleared='cleared'), PropertyMock(cleared='cleared'))
	assert t.cleared == 'reconciled'
	assert isinstance(t.category, Category)

