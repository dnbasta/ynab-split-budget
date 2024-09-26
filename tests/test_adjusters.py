from datetime import date
from unittest.mock import MagicMock, PropertyMock, patch

from ynabtransactionadjuster import Payee, Transaction
from ynabtransactionadjuster.models import Category

from ynabsplitbudget.adjusters import ReconcileAdjuster, SplitAdjuster, ClearAdjuster


def test_reconcile_filter():
	# Arrange
	ra = ReconcileAdjuster(credentials=MagicMock())
	# Act
	t = ra.filter([PropertyMock(cleared='cleared'), PropertyMock(cleared='uncleared'), PropertyMock(cleared='reconciled')])
	# Assert
	assert len(t) == 1


@patch('ynabsplitbudget.adjusters.ReconcileAdjuster.categories', new_callable=PropertyMock())
def test_reconcile_adjust(mock_categories):
	# Arrange
	ma = ReconcileAdjuster(credentials=MagicMock())
	mock_category = MagicMock(spec=Category)
	# Act
	t = ma.adjust(PropertyMock(cleared='cleared', category=mock_category),
				  PropertyMock(cleared='cleared', category=mock_category))
	mock_categories.fetch_by_name.assert_not_called()
	# Assert
	assert t.cleared == 'reconciled'
	assert isinstance(t.category, Category)


@patch('ynabsplitbudget.adjusters.ReconcileAdjuster.categories', new_callable=PropertyMock())
def test_reconcile_adjust_wo_category(mock_categories):
	# Arrange
	ma = ReconcileAdjuster(credentials=MagicMock())
	mock_categories.fetch_by_name.return_value = MagicMock(spec=Category)
	# Act
	t = ma.adjust(PropertyMock(cleared='cleared', category=None), PropertyMock(cleared='cleared', category=None))
	# Assert
	assert t.cleared == 'reconciled'
	assert isinstance(t.category, Category)


def test_split_subtransactions():
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id',
					   account_id='account_id', since=date(2024, 1, 1))
	f = sa.filter([PropertyMock(id='a', cleared='cleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[]),
				   PropertyMock(id='b', cleared='cleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[MagicMock()])])
	assert len(f) == 1
	assert f[0].id == 'a'

def test_split_cleared():
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id',
					   account_id='account_id', since=date(2024, 1, 1))
	f = sa.filter([PropertyMock(id='a', cleared='cleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[]),
				   PropertyMock(id='b', cleared='reconciled', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[]),
				   PropertyMock(id='c', cleared='uncleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[])
				   ])
	assert len(f) == 2
	assert f[0].id == 'a'
	assert f[1].id == 'b'

def test_split_flag():
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id',
					   account_id='account_id', since=date(2024, 1, 1))
	f = sa.filter([PropertyMock(id='a', cleared='cleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[]),
				   PropertyMock(id='b', cleared='cleared', flag_color=None, account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[])
				   ])
	assert len(f) == 1
	assert f[0].id == 'a'

def test_split_date():
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id',
					   account_id='account_id', since=date(2024, 1, 1))
	f = sa.filter([PropertyMock(id='a', cleared='cleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2024, 1, 1), subtransactions=[]),
				   PropertyMock(id='b', cleared='cleared', flag_color='red', account=MagicMock(id='account_idx'),
								transaction_date=date(2023, 1, 1), subtransactions=[])
				   ])
	assert len(f) == 1
	assert f[0].id == 'a'

@patch('ynabsplitbudget.adjusters.SplitAdjuster.payees', new_callable=PropertyMock())
def test_split_adjust(mock_payees):
	# Arrange
	sa = SplitAdjuster(credentials=MagicMock(), flag_color='red', transfer_payee_id='transfer_payee_id',
					   account_id='account_id', since=MagicMock(type=date))
	mock_payees.fetch_by_id.return_value = Payee(name='transfer_payee')
	# Act
	mt = sa.adjust(PropertyMock(category=Category(id='category_id', name='category_name'),
								amount=-1000,
								payee=Payee(name='payee_name'),
								memo='@25% memo'), PropertyMock())
	# Assert
	assert len(mt.subtransactions) == 2
	assert mt.subtransactions[0].amount == -250
	assert mt.subtransactions[0].payee.name == 'transfer_payee'
	assert mt.subtransactions[1].amount == -750
	assert mt.subtransactions[1].memo == '@25% memo'
	assert mt.subtransactions[1].category.name == 'category_name'


def test_clear_filter():
	ca = ClearAdjuster(credentials=MagicMock(), split_transaction_ids=['transaction_id'])
	r = ca.filter([PropertyMock(spec=Transaction, cleared='uncleared', id='transaction_id'),
				   PropertyMock(spec=Transaction, cleared='uncleared', id='transaction_id2'),
				   PropertyMock(spec=Transaction, cleared='cleared', id='transaction_id')])
	assert len(r) == 1


@patch('ynabsplitbudget.adjusters.ClearAdjuster.categories', new_callable=PropertyMock())
def test_clear_adjust(mock_categories):
	# Arrange
	ca = ClearAdjuster(credentials=MagicMock(), split_transaction_ids=[])
	mock_category = Category(name='category_name', id='category_id')
	# Act
	mt = ca.adjust(PropertyMock(cleared='uncleared', category=mock_category),
				   PropertyMock(cleared='uncleared', category=mock_category))
	# Assert
	mock_categories.fetch_by_name.assert_not_called()
	assert mt.cleared == 'cleared'
	assert mt.category == mock_category


@patch('ynabsplitbudget.adjusters.ClearAdjuster.categories', new_callable=PropertyMock())
def test_clear_adjust_wo_category(mock_categories):
	# Arrange
	ca = ClearAdjuster(credentials=MagicMock(), split_transaction_ids=[])
	mock_category = Category(name='category_name', id='category_id')
	mock_categories.fetch_by_name.return_value = mock_category
	# Act
	mt = ca.adjust(PropertyMock(cleared='uncleared', category=None), PropertyMock(cleared='uncleared', category=None))
	# Assert
	assert mt.cleared == 'cleared'
	assert mt.category == mock_category
