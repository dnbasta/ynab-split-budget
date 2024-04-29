from unittest.mock import MagicMock, PropertyMock, patch

from ynabtransactionadjuster import Payee
from ynabtransactionadjuster.models import Category

from ynabsplitbudget.adjusters import ReconcileAdjuster, SplitAdjuster


def test_reconcile_filter():

	ra = ReconcileAdjuster(credentials=MagicMock())
	# Act
	t = ra.filter([PropertyMock(cleared='cleared'), PropertyMock(cleared='uncleared'), PropertyMock(cleared='reconciled')])
	assert len(t) == 1


@patch('ynabsplitbudget.adjusters.ReconcileAdjuster.categories', new_callable=PropertyMock())
def test_reconcile_adjust(mock_categories):
	# Arrange
	ma = ReconcileAdjuster(credentials=MagicMock())
	mock_categories.fetch_by_name.return_value = MagicMock(spec=Category)
	t = ma.adjust(PropertyMock(cleared='cleared'), PropertyMock(cleared='cleared'))
	assert t.cleared == 'reconciled'
	assert isinstance(t.category, Category)


def test_split_filter():
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id')
	f = sa.filter([PropertyMock(cleared='cleared', flag_color='red', id='1'),
				   PropertyMock(cleared='cleared', id='2'),
				   PropertyMock(flag_color='yellow', id='3')])
	assert len(f) == 1
	assert f[0].id == '1'


@patch('ynabsplitbudget.adjusters.SplitAdjuster.payees', new_callable=PropertyMock())
def test_split_adjust(mock_payees):
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id')
	mock_payees.fetch_by_id.return_value = Payee(name='transfer_payee')

	mt = sa.adjust(PropertyMock(category=Category(id='category_id', name='category_name'),
								amount=-1000,
								payee=Payee(name='payee_name'),
								memo='@25% memo'), PropertyMock())

	assert len(mt.subtransactions) == 2
	assert mt.subtransactions[0].amount == -250
	assert mt.subtransactions[0].payee.name == 'transfer_payee'
	assert mt.subtransactions[1].amount == -750
	assert mt.subtransactions[1].memo == '@25% memo'
	assert mt.subtransactions[1].category.name == 'category_name'
