from unittest.mock import MagicMock, PropertyMock, patch

from ynabtransactionadjuster.models import Category

from ynabsplitbudget.adjusters import ReconcileAdjuster


def test_filter():

	ra = ReconcileAdjuster(credentials=MagicMock())
	# Act
	t = ra.filter([PropertyMock(cleared='cleared'), PropertyMock(cleared='uncleared'), PropertyMock(cleared='reconciled')])
	assert len(t) == 1


@patch('ynabsplitbudget.adjusters.ReconcileAdjuster.categories', new_callable=PropertyMock())
def test_adjust(mock_categories):
	# Arrange
	ma = ReconcileAdjuster(credentials=MagicMock())
	mock_categories.fetch_by_name.return_value = MagicMock(spec=Category)
	t = ma.adjust(PropertyMock(cleared='cleared'), PropertyMock(cleared='cleared'))
	assert t.cleared == 'reconciled'
	assert isinstance(t.category, Category)

