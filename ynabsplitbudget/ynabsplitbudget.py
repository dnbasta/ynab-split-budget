from pathlib import Path

import yaml

from ynabsplitbudget.client import BaseClient, SplitClient
from ynabsplitbudget.models.config import Config
from ynabsplitbudget.models.user import User
from ynabsplitbudget.syncrepository import SyncRepository


class YnabSplitBudget:
	def __init__(self, path: str):
		with Path(path).open(mode='r') as f:
			config_dict = yaml.safe_load(f)
		self._config = Config(user_1=UserLoader().load(config_dict['user_1']),
							  user_2=UserLoader().load(config_dict['user_2']))

	def _fetch_user(self, user_name: str):
		return next(u for u in (self._config.user_1, self._config.user_2) if u.name == user_name)

	def insert_complements(self, user_name: str) -> int:
		user = self._fetch_user(user_name)
		partner = self._config.user_1 if user == self._config.user_2 else self._config.user_2
		repo = SyncRepository(user=user, partner=partner)
		transactions = repo.fetch_new()

		repo.insert_complements(transactions)
		print(f'inserted {len(transactions)} complements into account from {partner.name}')
		return len(transactions)

	def split_transactions(self, user_name: str) -> int:
		c = SplitClient(self._fetch_user(user_name))
		st_list = c.fetch_new_to_split()
		[c.insert_split(st) for st in st_list]
		print(f'split {len(st_list)} transactions for {user_name}')
		return len(st_list)


class UserLoader:

	@staticmethod
	def load(user_dict: dict) -> User:
		c = BaseClient(token=user_dict['token'], user_name=user_dict['name'])
		account = c.fetch_account(budget_id=user_dict['budget'], account_id=user_dict['account'])
		return User(name=user_dict['name'], token=user_dict['token'], account=account, flag=user_dict['flag'])
