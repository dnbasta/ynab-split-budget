import pytest

from src.ynabsplitbudget.client import TransactionClient
from src.ynabsplitbudget.models.account import BaseAccount


@pytest.mark.parametrize('budget, account', [('bullshit', 'bullshit'), ('Daniel 09-19', 'bullshit')])
def test_fetch_account_fails(prod_conf, budget, account):
	client = TransactionClient.from_config(user=prod_conf.user_1)
	with pytest.raises(Exception) as e:
		client.fetch_account(budget_name=budget, account_name=account)


def test_fetch_account_passes(prod_conf):
	# Arrange
	client = TransactionClient.from_config(user=prod_conf.user_1)

	# Act
	a = client.fetch_account(budget_name='Daniel 09-19', account_name='Splitwise', user_name='Danny')
	assert isinstance(a, BaseAccount)
