from datetime import date, timedelta, datetime
from pathlib import Path
from typing import List

import yaml

from ynabsplitbudget.client import SplitClient, SyncClient
from ynabsplitbudget.models.exception import BalancesDontMatch
from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction
from ynabsplitbudget.syncrepository import SyncRepository
from ynabsplitbudget.userloader import UserLoader


class YnabSplitBudget:
	def __init__(self, path: str, user: str):
		userloader = UserLoader(path=path, user=user)
		self._user = userloader.user
		self._partner = userloader.partner

	def insert_complements(self, since: date = None) -> int:
		if since is None:
			since = datetime.now() - timedelta(days=30)

		repo = SyncRepository(user=self._user, partner=self._partner)
		transactions = repo.fetch_roots_wo_complement(since=since)

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
		repo = SyncRepository(user=self._user, partner=self._partner)
		user_balance, partner_balance = repo.fetch_balances()
		if user_balance + partner_balance != 0:
			raise BalancesDontMatch({'user': {'name': self._user.name,
											  'balance': user_balance},
									 'partner': {'name': self._partner.name,
												 'balance': partner_balance}})

	def delete_orphaned_complements(self) -> List[ComplementTransaction]:
		orphaned_complements = SyncRepository(user=self._user, partner=self._partner).find_orphaned_partner_complements()
		c = SyncClient(self._partner)
		[c.delete_complement(oc.id) for oc in orphaned_complements]
		print(f'deleted {len(orphaned_complements)} orphaned complements in account of {self._partner.name}')
		print(orphaned_complements)
		return orphaned_complements
