import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Union, Optional

from ynabsplitbudget.models.exception import SplitNotValid
from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.models.transaction import RootTransaction, ComplementTransaction, LookupTransaction
from ynabsplitbudget.models.user import User


@dataclass
class TransactionBuilder:
	user: User

	def build(self, t_dict: dict) -> Union[RootTransaction, ComplementTransaction, LookupTransaction]:
		if t_dict['import_id'] and 's||' in t_dict['import_id']:
			return self.build_complement(t_dict)
		if t_dict['account_id'] not in self.user.account.account_id:
			return self.build_lookup(t_dict)
		return self.build_root(t_dict)

	@staticmethod
	def build_root(t_dict: dict) -> RootTransaction:
		share_id = hashlib.shake_128(str(t_dict['id']).encode()).hexdigest(10)
		return RootTransaction(id=t_dict['id'],
							   transaction_date=datetime.strptime(t_dict['date'], '%Y-%m-%d').date(),
				   			   memo=t_dict['memo'],
				   			   payee_name=t_dict['payee_name'],
				   			   amount=t_dict['amount'],
				   			   account_id=t_dict['account_id'],
				   			   share_id=share_id)

	@staticmethod
	def build_complement(t_dict: dict) -> ComplementTransaction:
		regex = re.search(r's\|\|(.[^|]*)(?:\|\|)?(\d*)', t_dict['import_id']).groups()
		share_id = regex[0]
		iteration = int(regex[1]) if regex[1] != '' else 0
		return ComplementTransaction(id=t_dict['id'],
									 transaction_date=datetime.strptime(t_dict['date'], '%Y-%m-%d').date(),
									 memo=t_dict['memo'],
									 payee_name=t_dict['payee_name'],
									 amount=t_dict['amount'],
									 account_id=t_dict['account_id'],
									 share_id=share_id,
									 iteration=iteration)

	@staticmethod
	def build_lookup(t_dict: dict) -> LookupTransaction:

		# values if transaction is Transfer
		if t_dict['transfer_transaction_id']:
			tt_ids = [t_dict['transfer_transaction_id']]
			payee_name = t_dict['import_payee_name']

		# values if transaction is split
		else:
			tt_ids = [st['transfer_transaction_id'] for st in t_dict['subtransactions']
					  if st['transfer_transaction_id'] is not None]
			payee_name = t_dict['payee_name']

		return LookupTransaction(payee_name=payee_name,
				   transfer_transaction_ids=tt_ids,
				   account_id=t_dict['account_id'])


class SplitTransactionBuilder:

	@staticmethod
	def build(t_dict: dict) -> Optional[SplitTransaction]:
		try:
			split_amount = SplitParser().parse_split(t_dict)
			return SplitTransaction.from_dict(t_dict=t_dict, split_amount=split_amount)
		except SplitNotValid as e:
			logging.error(e)
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
