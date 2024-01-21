import hashlib
import re
from dataclasses import dataclass
from typing import Union, Optional

from ynabsplitbudget.models.exception import SplitNotValid
from ynabsplitbudget.models.splittransaction import SplitTransaction
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


class SplitTransactionBuilder:

	@staticmethod
	def build(t_dict: dict) -> Optional[SplitTransaction]:
		try:
			split_amount = SplitParser().parse_split(t_dict)
			return SplitTransaction.from_dict(t_dict=t_dict, split_amount=split_amount)
		except SplitNotValid as e:
			print(e)
			return None


class SplitParser:

	@staticmethod
	def parse_split(t_dict: dict) -> int:
		amount = t_dict['amount']
		rep = f"[{t_dict['date']} | {t_dict['payee_name']} | {amount / 1000:.2f} | {t_dict['memo']}]"

		try:
			r = re.search(r'@(\d+\.?\d*)(%?)', t_dict['memo'])
		except TypeError:
			r = None

		# return half the amount if no split attribution is found
		if r is None:
			return amount * 0.5

		split_number = float(r.groups()[0])
		if r.groups()[1] == '%':
			if split_number <= 100:
				return amount * split_number / 100
			raise SplitNotValid(f"Split is above 100% for transaction {rep}")
		if split_number * 1000 > abs(amount):
			raise SplitNotValid(f"Split is above total amount of {amount / 1000:.2f} for transaction {rep}")
		sign = -1 if amount < 0 else 1
		return int(sign * split_number * 1000)
