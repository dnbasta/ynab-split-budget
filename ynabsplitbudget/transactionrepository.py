from dataclasses import dataclass, field
from typing import List, Optional

from ynabsplitbudget.client import SyncClient
from ynabsplitbudget.models.config import Config
from ynabsplitbudget.models.transaction import Transaction, RootTransaction, ComplementTransaction, LookupTransaction


@dataclass
class TransactionRepository:
	config: Config
	user_1: List[RootTransaction] = field(default_factory=lambda: [])
	user_2: List[RootTransaction] = field(default_factory=lambda: [])

	def populate(self):
		u1c = SyncClient(user=self.config.user_1)
		u2c = SyncClient(user=self.config.user_2)

		# fetch changed
		u1t = u1c.fetch_new()
		u2t = u2c.fetch_new()

		# fetch lookup records
		try:
			lookup_date = min([t.transaction_date for t in u1t] +
							  [t.transaction_date for t in u2t])
			u1l = u1c.fetch_lookup(lookup_date)
			u2l = u2c.fetch_lookup(lookup_date)

			self.user_1 = [self._put_original_payee(t, u1l) for t in u1t if self._find_child(t, u2l) is None]
			self.user_2 = [self._put_original_payee(t, u2l) for t in u2t if self._find_child(t, u1l) is None]
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
