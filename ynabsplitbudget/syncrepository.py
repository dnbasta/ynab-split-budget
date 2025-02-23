from datetime import date
from typing import List, Union

from session import Session
from ynabsplitbudget.client import Client
from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction, LookupTransaction
from ynabsplitbudget.models.user import User


class SyncRepository:

	def __init__(self, user: User, partner: User, session: Session):
		self._user_client = Client(budget_id=user.budget_id, account_id=user.account_id,
								   user_name=user.name, session=session)
		self._partner_client = Client(budget_id=partner.budget_id, account_id=partner.account_id,
									  user_name=partner.name, session=session)

	def fetch_roots_wo_complement(self, since: date, include_uncleared: bool) -> List[RootTransaction]:
		roots = self._user_client.fetch_roots(since=since, include_uncleared=include_uncleared)
		pl = [t for t in self._partner_client.fetch_lookup(since) if isinstance(t, ComplementTransaction)]
		roots_wo_complement = [t for t in roots if t.share_id not in [lo.share_id for lo in pl]]
		transactions_replaced_payee = self.replace_payee(transactions=roots_wo_complement,
															 lookup_date=since)
		return transactions_replaced_payee

	def insert_complements(self, transactions: List[RootTransaction]) -> List[ComplementTransaction]:
		return [self._partner_client.insert_complement(t) for t in transactions]

	def replace_payee(self, transactions: List[RootTransaction], lookup_date: date) -> List[RootTransaction]:
		ul = self._user_client.fetch_lookup(lookup_date)
		pr = PayeeReplacer(lookup=ul)
		transactions_replaced = [pr.replace(t) for t in transactions]
		return transactions_replaced

	def find_orphaned_partner_complements(self, since: date) -> List[ComplementTransaction]:
		current_complements = [lo for lo in self._partner_client.fetch_lookup(since=since) if isinstance(lo, ComplementTransaction)]
		current_roots = [cr for cr in self._user_client.fetch_roots(since=since, include_uncleared=True)]
		orphaned_complements = [c for c in current_complements if c.share_id not in [d.share_id for d in current_roots]]
		return orphaned_complements

	def fetch_balances(self) -> (int, int):
		user_balance = self._user_client.fetch_balance()
		partner_balance = self._partner_client.fetch_balance()
		return user_balance, partner_balance


class PayeeReplacer:

	def __init__(self, lookup: List[Union[RootTransaction, ComplementTransaction, LookupTransaction]]):
		lookup_filtered = [lu for lu in lookup if isinstance(lu, LookupTransaction)]
		self._lookup_dict = {ti: lu.payee_name for lu in lookup_filtered for ti in lu.transfer_transaction_ids}

	def replace(self, t: RootTransaction) -> RootTransaction:
		if t.id in self._lookup_dict.keys():
			t.payee_name = self._lookup_dict[t.id]
		return t
