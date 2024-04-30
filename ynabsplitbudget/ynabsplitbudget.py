import logging
from datetime import date, timedelta, datetime
from typing import List, Optional

from ynabtransactionadjuster import Credentials

from ynabsplitbudget.adjusters import ReconcileAdjuster, SplitAdjuster, ClearAdjuster
from ynabsplitbudget.client import SyncClient
from ynabsplitbudget.fileloader import FileLoader
from ynabsplitbudget.models.exception import BalancesDontMatch
from ynabsplitbudget.models.transaction import ComplementTransaction
from ynabsplitbudget.syncrepository import SyncRepository
from ynabsplitbudget.userloader import UserLoader


class YnabSplitBudget:

	def __init__(self, config: dict, user: str):
		self.logger = self._set_up_logger()

		userloader = UserLoader(config_dict=config)
		self._user = userloader.load(user)
		self._partner = userloader.load_partner(user)

	@classmethod
	def from_yaml(cls, path: str, user: str):
		config_dict = FileLoader(path).load()
		return cls(config=config_dict, user=user)

	def insert_complements(self, since: date = None) -> int:
		since = self._substitute_default_since(since)
		repo = SyncRepository(user=self._user, partner=self._partner)
		transactions = repo.fetch_roots_wo_complement(since=since)

		repo.insert_complements(transactions)
		logging.getLogger(__name__).info(f'inserted {len(transactions)} complements into account of {self._partner.name}')
		return len(transactions)

	def split_transactions(self, clear_splits: bool = False) -> int:
		"""Splits transactions """
		creds = Credentials(token=self._user.token, budget=self._user.account.budget_id)
		s = SplitAdjuster(creds, flag_color=self._user.flag, transfer_payee_id=self._user.account.transfer_payee_id,
						  account_id=self._user.account.account_id)
		mod_trans = s.apply()
		updated_transactions = s.update(mod_trans)
		logging.getLogger(__name__).info(f'split {len(updated_transactions)} transactions for {self._user.name}')

		if clear_splits:
			transfer_transaction_ids = [st.transfer_transaction_id for t in updated_transactions for st in
										t.subtransactions if st.transfer_transaction_id]
			creds = Credentials(token=self._user.token, budget=self._user.account.budget_id,
								account=self._user.account.account_id)
			ca = ClearAdjuster(creds, split_transaction_ids=transfer_transaction_ids)
			mod_trans_clear = ca.apply()
			count_clear = len(s.update(mod_trans_clear))
			logging.getLogger(__name__).info(f'cleared {count_clear} transactions for {self._user.name}')

		return len(updated_transactions)

	def raise_on_balances_off(self):
		repo = SyncRepository(user=self._user, partner=self._partner)
		user_balance, partner_balance = repo.fetch_balances()
		if user_balance + partner_balance != 0:
			raise BalancesDontMatch({'user': {'name': self._user.name,
											  'balance': user_balance},
									 'partner': {'name': self._partner.name,
												 'balance': partner_balance}})

	def delete_orphaned_complements(self, since: date = None) -> List[ComplementTransaction]:
		since = self._substitute_default_since(since)
		orphaned_complements = SyncRepository(user=self._user, partner=self._partner).find_orphaned_partner_complements(since)
		c = SyncClient(self._partner)
		[c.delete_complement(oc.id) for oc in orphaned_complements]
		logging.getLogger(__name__).info(f'deleted {len(orphaned_complements)} orphaned complements in account of {self._partner.name}')
		logging.getLogger(__name__).info(orphaned_complements)
		return orphaned_complements

	def reconcile(self) -> int:
		"""Reconciles cleared transactions in the current account
		:return: count of reconciled transactions
		"""
		creds = Credentials(token=self._user.token, budget=self._user.account.budget_id,
							account=self._user.account.account_id)
		adjuster = ReconcileAdjuster.from_credentials(creds)
		c = adjuster.dryrun()
		logging.getLogger(__name__).info(f'reconciled {c} transactions for {self._user.name}')
		return c

	@staticmethod
	def _substitute_default_since(since: Optional[date]):
		if since is None:
			return datetime.now() - timedelta(days=30)
		return since

	@staticmethod
	def _set_up_logger() -> logging.Logger:
		parent_name = '.'.join(__name__.split('.')[:-1])
		logger = logging.getLogger(parent_name)
		logger.setLevel(20)
		return logger
