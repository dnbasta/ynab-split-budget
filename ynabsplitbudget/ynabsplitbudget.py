from pathlib import Path

import yaml

from ynabsplitbudget.client import BaseClient, SyncClient, SplitClient
from ynabsplitbudget.models.config import Config
from ynabsplitbudget.models.user import User
from ynabsplitbudget.transactionrepository import TransactionRepository


class YnabSplitBudget:
	def __init__(self, path: str):
		with Path(path).open(mode='r') as f:
			config_dict = yaml.safe_load(f)
		self._config = Config(user_1=self._load_user(config_dict['user_1']),
							  user_2=self._load_user(config_dict['user_2']))

	@staticmethod
	def _load_user(user_dict: dict) -> User:
		account = BaseClient().fetch_account(budget_name=user_dict['budget'],
										  account_name=user_dict['account'],
										  user_name=user_dict['name'],
										  token=user_dict['token'])
		return User(name=user_dict['name'], token=user_dict['token'], account=account,
					flag=user_dict['flag'])

	def _fetch_user(self, user_name: str):
		return next(u for u in (self._config.user_1, self._config.user_2) if u.name == user_name)

	def insert_complements(self, user_name: str) -> int:
		user = self._fetch_user(user_name)
		partner = self._config.user_1 if user == self._config.user_2 else self._config.user_2
		st_repo = TransactionRepository(user=user, partner=partner).populate()
		c = SyncClient(partner)

		[c.insert_complement(t) for t in st_repo.transactions]
		print(f'inserted {len(st_repo.transactions)} complements into account from {partner.name}')
		return len(st_repo.transactions)

	def split_transactions(self, user_name: str) -> int:
		c = SplitClient(self._fetch_user(user_name))
		st_list = c.fetch_new_to_split()
		[c.insert_split(st) for st in st_list]
		print(f'split {len(st_list)} transactions for {user_name}')
		return len(st_list)