from dataclasses import dataclass
from typing import List, Optional

from ynabsplitaccount.client import TransactionClient
from ynabsplitaccount.models.config import Config
from ynabsplitaccount.models.transaction import Transaction, RootTransaction, ComplementTransaction


@dataclass
class TransactionRepository:
	user_1_changed: List[Transaction]
	user_2_changed: List[Transaction]
	user_1_lookup: List[Transaction]
	user_2_lookup: List[Transaction]

	@classmethod
	def from_config(cls, config: Config):
		u1c = TransactionClient(user=config.user_1)
		u2c = TransactionClient(user=config.user_2)

		# fetch changed
		u1t = u1c.fetch_changed()
		u2t = u2c.fetch_changed()

		# fetch lookup records
		try:
			lookup_date = min([t.transaction_date for t in u1t] + [t.transaction_date for t in u2t])
			u1l = u1c.fetch_lookup(lookup_date)
			u2l = u2c.fetch_lookup(lookup_date)
		except ValueError:
			u1l = []
			u2l = []

		return cls(user_1_changed=u1t,
				   user_2_changed=u2t,
				   user_1_lookup=u1l,
				   user_2_lookup=u2l)

	def fetch_new_user_1(self) -> List[RootTransaction]:
		return [t for t in self.user_1_changed if isinstance(t, RootTransaction) and self._find_child(t) is None]

	def fetch_new_user_2(self) -> List[RootTransaction]:
		return [t for t in self.user_2_changed if isinstance(t, RootTransaction) and self._find_child(t) is None]

	def _find_child(self, t: RootTransaction) -> Optional[ComplementTransaction]:
		return next((c for c in self.user_1_lookup + self.user_2_lookup
					 if isinstance(c, ComplementTransaction) and c.share_id == t.share_id), None)
