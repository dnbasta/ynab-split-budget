from pathlib import Path

import yaml

from ynabsplitbudget.client import SplitClient, SyncClient
from ynabsplitbudget.models.exception import BalancesDontMatch
from ynabsplitbudget.syncrepository import SyncRepository
from ynabsplitbudget.userloader import UserLoader


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



