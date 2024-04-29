import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Union, Optional

from ynabsplitbudget.models.exception import SplitNotValid
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


