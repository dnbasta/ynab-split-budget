from unittest.mock import MagicMock, patch

import pytest

from ynabsplitbudget import YnabSplitBudget
from ynabsplitbudget.models.exception import BalancesDontMatch


@patch('ynabsplitbudget.ynabsplitbudget.SyncRepository.fetch_balances')
def test_raise_on_balances_off_raise(mock_repository):
	# Arrange
	mock_repository.return_value = (100, -50)
	ysb = YnabSplitBudget(user=MagicMock(), partner=MagicMock())
	with pytest.raises(BalancesDontMatch):
		ysb.raise_on_balances_off()

@patch('ynabsplitbudget.ynabsplitbudget.SyncRepository.fetch_balances')
def test_raise_on_balances_off_dont_raise(mock_repository):
	# Arrange
	mock_repository.return_value = (100, -100)
	ysb = YnabSplitBudget(user=MagicMock(), partner=MagicMock())
	ysb.raise_on_balances_off()
