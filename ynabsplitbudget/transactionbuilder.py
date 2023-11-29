import hashlib
import re
from dataclasses import dataclass
from typing import Union

from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction, LookupTransaction
from ynabsplitbudget.models.user import User


@dataclass
class TransactionBuilder:
	user: User

	def build_root_transaction(self, t_dict: dict) -> RootTransaction:
		return RootTransaction.from_dict(t_dict=t_dict, share_id=self._encrypt(t_dict['id']))

	def build(self, t_dict: dict) -> Union[RootTransaction, ComplementTransaction, LookupTransaction]:
		if t_dict['import_id'] and 's||' in t_dict['import_id']:
			share_id = re.search(r's\|\|(.[^-]*)', t_dict['import_id'])[1]
			return ComplementTransaction.from_dict(t_dict=t_dict, share_id=share_id)

		if t_dict['account_id'] not in self.user.account.account_id:
			return LookupTransaction.from_dict(t_dict)

		return self.build_root_transaction(t_dict)

	@staticmethod
	def _encrypt(val: str) -> str:
		return hashlib.shake_128(str(val).encode()).hexdigest(10)
