import logging
from datetime import date, timedelta, datetime
from typing import List, Optional

from ynabtransactionadjuster import Credentials, Transaction

from ynabsplitbudget.adjusters import SplitAdjuster
from ynabsplitbudget.client import Client
from ynabsplitbudget.models.exception import BalancesDontMatch
from ynabsplitbudget.models.transaction import ComplementTransaction
from ynabsplitbudget.models.user import User
from ynabsplitbudget.syncrepository import SyncRepository


class YnabSplitBudget:
	"""Interface to YNAB Split Budget.

	:ivar user: User to use for instance
	:ivar partner: Partner to use for instance
	:ivar logger: Logger of the instance
	"""
	def __init__(self, user: User, partner: User):
		self.user = user
		self.partner = partner
		self.logger = self._set_up_logger()

	def push(self, include_uncleared: bool = False, since: date = None) -> List[ComplementTransaction]:
		"""Pushes transactions from user split account to partner split account. By default, considers transactions of
		last 30 days.

		:param include_uncleared: If set to True, will also consider uncleared transactions
		:param since: If set to date, will push transactions from that date onwards instead of default 30 days
		:return: List of inserted transactions in partner split account
		"""
		since = self._substitute_default_since(since)
		repo = SyncRepository(user=self.user, partner=self.partner, include_uncleared=include_uncleared)
		transactions = repo.fetch_roots_wo_complement(since=since)

		complement_transactions = repo.insert_complements(transactions)
		logging.getLogger(__name__).info(f'inserted {len(complement_transactions)} complements into account of '
										 f'{self.partner.name}')
		return complement_transactions

	def split(self) -> List[Transaction]:
		"""Splits transactions (by default 50%) into subtransaction with original category and transfer subtransaction
		to split account

		:return: list with split transactions
		"""
		creds = Credentials(token=self.user.token, budget=self.user.budget_id)
		s = SplitAdjuster(creds, flag_color=self.user.flag_color,
						  transfer_payee_id=self.user.fetch_account().transfer_payee_id,
						  account_id=self.user.account_id)
		mod_trans = s.apply()
		updated_transactions = s.update(mod_trans)
		logging.getLogger(__name__).info(f'split {len(updated_transactions)} transactions for {self.user.name}')

		return updated_transactions

	def raise_on_balances_off(self):
		"""Evaluates cleared balances in both accounts

		:raises BalancesDontMatch: if cleared amounts in both accounts don't match
		"""
		repo = SyncRepository(user=self.user, partner=self.partner)
		user_balance, partner_balance = repo.fetch_balances()
		if user_balance + partner_balance != 0:
			raise BalancesDontMatch({'user': {'name': self.user.name,
											  'balance': user_balance},
									 'partner': {'name': self.partner.name,
												 'balance': partner_balance}})

	def delete_orphans(self, since: date = None) -> List[ComplementTransaction]:
		"""Delete orphaned transactions in partner account. By default, considers transactions of last 30 days.

		:param since: if set to date will delete orphaned transactions from that date onwards instead of default 30 days
		"""
		since = self._substitute_default_since(since)
		orphaned_complements = SyncRepository(user=self.user, partner=self.partner).find_orphaned_partner_complements(since)
		c = Client(user_name=self.partner.name, budget_id=self.partner.budget_id, account_id=self.partner.account_id,
				   token=self.partner.token)
		[c.delete_complement(oc.id) for oc in orphaned_complements]
		logging.getLogger(__name__).info(f'deleted {len(orphaned_complements)} orphaned complements in account of {self.partner.name}')
		logging.getLogger(__name__).info(orphaned_complements)
		return orphaned_complements

	@staticmethod
	def _substitute_default_since(since: Optional[date]) -> date:
		if since is None:
			return datetime.now() - timedelta(days=30)
		return since

	@staticmethod
	def _set_up_logger() -> logging.Logger:
		parent_name = '.'.join(__name__.split('.')[:-1])
		logger = logging.getLogger(parent_name)
		logger.setLevel(20)
		return logger
