from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from ynabtransactionadjuster import ModifiedTransaction

from models.transaction import RootTransaction
from ynabsplitbudget import YnabSplitBudget
from ynabsplitbudget.models.exception import BalancesDontMatch


@patch('ynabsplitbudget.ynabsplitbudget.SyncRepository.fetch_balances')
def test_raise_on_balances_off_raise(mock_repository):
	# Arrange
	mock_repository.return_value = (100, -50)
	ysb = YnabSplitBudget(user=MagicMock(), partner=MagicMock(), since=MagicMock(type=date))
	with pytest.raises(BalancesDontMatch):
		ysb.raise_on_balances_off()

@patch('ynabsplitbudget.ynabsplitbudget.SyncRepository.fetch_balances')
def test_raise_on_balances_off_dont_raise(mock_repository):
	# Arrange
	mock_repository.return_value = (100, -100)
	ysb = YnabSplitBudget(user=MagicMock(), partner=MagicMock(), since=MagicMock(type=date))
	ysb.raise_on_balances_off()

@patch('ynabsplitbudget.adjusters.SplitAdjuster.apply')
def test_split_preview(mock_adjuster):
	# Arrange
	mock_transaction = MagicMock(type=ModifiedTransaction)
	mock_adjuster.return_value = [mock_transaction]
	ysb = YnabSplitBudget(user=MagicMock(), partner=MagicMock(), since=MagicMock(type=date))
	# Act
	mt = ysb.split_preview()
	# Assert
	assert len(mt) == 1
	assert mt[0] == mock_transaction

@patch('ynabsplitbudget.ynabsplitbudget.SyncRepository.fetch_roots_wo_complement')
def test_push_preview(mock_repo):
	# Arrange
	mock_transaction = MagicMock(type=RootTransaction)
	mock_repo.return_value = [mock_transaction]
	ysb = YnabSplitBudget(user=MagicMock(), partner=MagicMock(), since=MagicMock(type=date))
	# Act
	rt = ysb.push_preview()
	# Assert
	assert len(rt) == 1
	assert rt[0] == mock_transaction