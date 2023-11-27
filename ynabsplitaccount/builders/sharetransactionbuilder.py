import hashlib
import re

from ynabsplitaccount.models.sharetransaction import ShareTransactionParent, ShareTransactionChild


class ShareTransactionBuilder:

	def build(self, t_dict: dict):
		if t_dict['import_id'] and 's||' in t_dict['import_id']:
			share_id = re.search(r's\|\|(.[^-]*)', t_dict['import_id'])[1]
			return ShareTransactionChild.from_dict(t_dict=t_dict, share_id=share_id)
		return ShareTransactionParent.from_dict(t_dict=t_dict, share_id=self._encrypt(t_dict['id']))

	@staticmethod
	def _encrypt(val: str) -> str:
		return hashlib.shake_128(str(val).encode()).hexdigest(10)