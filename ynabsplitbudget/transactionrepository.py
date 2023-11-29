from dataclasses import dataclass, field
from typing import List, Optional

from ynabsplitbudget.client import SyncClient
from ynabsplitbudget.models.transaction import Transaction, RootTransaction, ComplementTransaction, LookupTransaction
from ynabsplitbudget.models.user import User


@dataclass
class TransactionRepository:
	user: User
	partner: User
	transactions: List[RootTransaction] = field(default_factory=lambda: [])

	def populate(self):
		uc = SyncClient(user=self.user)
		pc = SyncClient(user=self.partner)

		# fetch changed
		ut = uc.fetch_new()

		# fetch lookup records
		try:
			lookup_date = min([t.transaction_date for t in ut])
			ul = uc.fetch_lookup(lookup_date)
			pl = pc.fetch_lookup(lookup_date)

			self.transactions = [self._put_original_payee(t, ul) for t in ut if self._find_child(t, pl) is None]
		except ValueError:
			pass

		return self

	@staticmethod
	def _find_child(t: RootTransaction, lookup: List[Transaction]) -> Optional[ComplementTransaction]:
		return next((c for c in lookup
					 if isinstance(c, ComplementTransaction) and c.share_id == t.share_id), None)

	@staticmethod
	def _put_original_payee(t: RootTransaction, lookup: List[Transaction]) -> RootTransaction:
		lookups = [lu for lu in lookup if isinstance(lu, LookupTransaction)]
		lookup_dict = {ti: lu.payee_name for lu in lookups for ti in lu.transfer_transaction_ids}
		if t.id in lookup_dict.keys():
			t.payee_name = lookup_dict[t.id]
		return t
