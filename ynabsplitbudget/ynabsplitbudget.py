from pathlib import Path

import yaml

from ynabsplitbudget.client import BaseClient, SplitClient
from ynabsplitbudget.models.exception import UserNotFound
from ynabsplitbudget.models.user import User
from ynabsplitbudget.syncrepository import SyncRepository


class YnabSplitBudget:
	def __init__(self, path: str, user: str):
		self._userloader = UserLoader(path=path)
		self._user = self._userloader.load(user)

	def insert_complements(self, partner: str) -> int:
		partner = self._userloader.load(partner)
		repo = SyncRepository(user=self._user, partner=partner)
		transactions = repo.fetch_new()

		repo.insert_complements(transactions)
		print(f'inserted {len(transactions)} complements into account of {partner.name}')
		return len(transactions)

	def split_transactions(self) -> int:
		c = SplitClient(self._user)
		st_list = c.fetch_new_to_split()
		[c.insert_split(st) for st in st_list]
		print(f'split {len(st_list)} transactions for {self._user.name}')
		return len(st_list)


class UserLoader:

	def __init__(self, path: str):
		self._path = path
		with Path(path).open(mode='r') as f:
			self._config_dict = yaml.safe_load(f)

	def load(self, user: str) -> User:

		try:
			user_dict = self._config_dict[user]
			c = BaseClient(token=user_dict['token'], user_name=user)
			account = c.fetch_account(budget_id=user_dict['budget'], account_id=user_dict['account'])
			return User(name=user, token=user_dict['token'], account=account, flag=user_dict['flag'])

		except KeyError:
			raise UserNotFound(f"{user} not found in config file at {self._path}")


