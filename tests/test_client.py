import pytest
from src.ynabsplitbudget.client import TransactionClient
from src.ynabsplitbudget.config import Config


@pytest.mark.parametrize('budget, account', [('bullshit', 'bullshit'), ('Daniel 09-19', 'bullshit')])
def test_fetch_account_fails(prod_conf, budget, account):
	c = Config.from_path(path=prod_conf)
	client = TransactionClient.from_config(user=c.user_1, last_server_knowledge=c.server_knowledge.user_1)
	with pytest.raises(Exception) as e:
		client.fetch_account(budget_name=budget, account_name=account)


def test_fetch_account_passes(prod_conf):
	# Arrange
	c = Config.from_path(path=prod_conf)
	client = TransactionClient.from_config(user=c.user_1, last_server_knowledge=c.server_knowledge.user_1)

	# Act
	a = client.fetch_account(budget_name='Daniel 09-19', account_name='Splitwise')
	assert isinstance(a, Account)