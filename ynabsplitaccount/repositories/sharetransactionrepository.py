from dataclasses import dataclass
from typing import List, Optional

from ynabsplitaccount.client import ShareTransactionClient
from ynabsplitaccount.models.config import Config
from ynabsplitaccount.models.sharetransaction import ShareTransaction, ShareTransactionParent, ShareTransactionChild


@dataclass
class ShareTransactionRepository:
	user_1_changed: List[ShareTransaction]
	user_2_changed: List[ShareTransaction]
	user_1_lookup: List[ShareTransaction]
	user_2_lookup: List[ShareTransaction]
	user_1_server_knowledge: int
	user_2_server_knowledge: int

	@classmethod
	def from_config(cls, config: Config):
		u1c = ShareTransactionClient(user=config.user_1)
		u2c = ShareTransactionClient(user=config.user_2)

		# fetch changed
		u1t, u1sk = u1c.fetch_changed()
		u2t, u2sk = u2c.fetch_changed()

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
				   user_2_lookup=u2l,
				   user_1_server_knowledge=u1sk,
				   user_2_server_knowledge=u2sk)

	def fetch_new_user_1(self) -> List[ShareTransactionParent]:
		return [t for t in self.user_1_changed if isinstance(t, ShareTransactionParent) and self._find_child(t) is None]

	def fetch_new_user_2(self) -> List[ShareTransactionParent]:
		return [t for t in self.user_2_changed if isinstance(t, ShareTransactionParent) and self._find_child(t) is None]

	def _find_child(self, t: ShareTransactionParent) -> Optional[ShareTransactionChild]:
		return next((c for c in self.user_1_lookup + self.user_2_lookup
			  if isinstance(c, ShareTransactionChild) and c.share_id == t.share_id), None)
