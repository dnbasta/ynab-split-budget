from pathlib import Path

import yaml

from ynabsplitbudget.client import BaseClient, SplitClient, SyncClient
from ynabsplitbudget.models.exception import UserNotFound, BalancesDontMatch, ConfigNotValid
from ynabsplitbudget.models.user import User
from ynabsplitbudget.syncrepository import SyncRepository


class YnabSplitBudget:
	def __init__(self, path: str, user: str):
		userloader = UserLoader(path=path, user=user)
		self._user = userloader.user
		self._partner = userloader.partner

	def insert_complements(self) -> int:
		repo = SyncRepository(user=self._user, partner=self._partner)
		transactions = repo.fetch_new()

		repo.insert_complements(transactions)
		print(f'inserted {len(transactions)} complements into account of {self._partner.name}')
		return len(transactions)

	def split_transactions(self) -> int:
		c = SplitClient(self._user)
		st_list = c.fetch_new_to_split()
		[c.insert_split(st) for st in st_list]
		print(f'split {len(st_list)} transactions for {self._user.name}')
		return len(st_list)

	def raise_on_balances_off(self):
		user_balance = SyncClient(user=self._user).fetch_balance()
		partner_balance = SyncClient(user=self._partner).fetch_balance()

		if user_balance + partner_balance != 0:
			raise BalancesDontMatch({'user': {'name': self._user.name, 'balance': user_balance},
									 'partner': {'name': self._partner.name, 'balance': partner_balance}})


class UserLoader:

	def __init__(self, path: str, user: str):
		self._path = path
		self._user_name = user
		with Path(path).open(mode='r') as f:
			self._config_dict = yaml.safe_load(f)

		if len(self._config_dict) != 2:
			raise ConfigNotValid('Config needs to have exactly 2 user entries')

		for u, entries in self._config_dict.items():
			for e in ['account', 'budget', 'token', 'flag']:
				if e not in entries.keys():
					raise ConfigNotValid(f"'{e}' missing for user '{u}'")

	def load(self, user) -> User:

		try:
			user_dict = self._config_dict[user]
			c = BaseClient(token=user_dict['token'], user_name=user)
			account = c.fetch_account(budget_id=user_dict['budget'], account_id=user_dict['account'])
			return User(name=user, token=user_dict['token'], account=account, flag=user_dict['flag'])

		except KeyError:
			raise UserNotFound(f"{user} not found in config file at {self._path}")

	@property
	def user(self) -> User:
		return self.load(self._user_name)

	@property
	def partner(self) -> User:
		partner_name = next(u for u in self._config_dict.keys() if u != self._user_name)
		return self.load(partner_name)
