import pytest

from ynabsplitbudget.models.exception import SplitNotValid
from ynabsplitbudget.transactionbuilder import SplitParser


@pytest.mark.parametrize('test_input, expected', [('xxx', -1000), ('xxx @25%:xxx', -500), ('@33%', -660), ('@0.7', -700),
												  (None, -1000)])
def test_parse_split_pass(test_input, expected):
	# Arrange
	c = SplitParser()
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': -2000, 'memo': test_input}

	# Act
	split_amount = c.parse_split(t_dict)

	# Assert
	assert split_amount == expected


@pytest.mark.parametrize('test_input', ['@110%', '@2'])
def test_parse_split_fail(test_input):
	# Arrange
	c = SplitParser()
	t_dict = {'date': '2023-12-01', 'payee_name': 'payee', 'amount': -1000, 'memo': test_input}

	# Assert
	with pytest.raises(SplitNotValid):
		# Act
		c.parse_split(t_dict)
