from typing import List, Optional

from ynabsplitbudget.client import SyncClient
from ynabsplitbudget.models.transaction import Transaction, RootTransaction, ComplementTransaction, LookupTransaction
from ynabsplitbudget.models.user import User


class SyncRepository:

	def __init__(self, user: User, partner: User):
		self._user_client = SyncClient(user)
		self._partner_client = SyncClient(partner)

	def fetch_new(self) -> List[RootTransaction]:
		ut = self._user_client.fetch_new()

		try:
			# fetch lookup records
			lookup_date = min([t.transaction_date for t in ut])
			ul = self._user_client.fetch_lookup(lookup_date)
			pl = self._partner_client.fetch_lookup(lookup_date)

			# Filter for transactions without child
			cf = ChildFinder(lookup=pl)
			transactions_wo_child = [t for t in ut if cf.find(t) is None]

			# Replace payee with original one in case of split transaction
			pr = PayeeReplacer(lookup=ul)
			transactions = [pr.replace(t) for t in transactions_wo_child]

			return transactions

		except ValueError:
			return []

	def insert_complements(self, transactions: List[RootTransaction]):
		[self._partner_client.insert_complement(t) for t in transactions]


class ChildFinder:

	def __init__(self, lookup: List[Transaction]):
		self._lookup = [l for l in lookup if isinstance(l, ComplementTransaction)]

	def find(self, t: RootTransaction) -> Optional[ComplementTransaction]:
		return next((c for c in self._lookup if c.share_id == t.share_id), None)


class PayeeReplacer:

	def __init__(self, lookup: List[Transaction]):
		lookup_filtered = [lu for lu in lookup if isinstance(lu, LookupTransaction)]
		self._lookup_dict = {ti: lu.payee_name for lu in lookup_filtered for ti in lu.transfer_transaction_ids}

	def replace(self, t: RootTransaction) -> RootTransaction:
		if t.id in self._lookup_dict.keys():
			t.payee_name = self._lookup_dict[t.id]
		return t
