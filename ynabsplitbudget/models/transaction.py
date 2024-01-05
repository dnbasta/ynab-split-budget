from dataclasses import dataclass
from datetime import date, datetime
from typing import List


@dataclass
class Transaction:
	id: str
	share_id: str
	transaction_date: date
	memo: str
	payee_name: str
	amount: float
	account_id: str

	@classmethod
	def from_dict(cls, t_dict: dict, share_id: str):
		return cls(id=t_dict['id'],
				   transaction_date=datetime.strptime(t_dict['date'], '%Y-%m-%d').date(),
				   memo=t_dict['memo'],
				   payee_name=t_dict['payee_name'],
				   amount=t_dict['amount'],
				   account_id=t_dict['account_id'],
				   share_id=share_id)


@dataclass
class RootTransaction(Transaction):
	pass


@dataclass
class ComplementTransaction(Transaction):
	pass


@dataclass
class LookupTransaction:
	account_id: str
	payee_name: str
	transfer_transaction_ids: List[str]

	@classmethod
	def from_dict(cls, t_dict: dict):
		tt_ids = [st['transfer_transaction_id'] for st in t_dict['subtransactions']
				  if st['transfer_transaction_id'] is not None]
		return cls(payee_name=t_dict['payee_name'],
				   transfer_transaction_ids=tt_ids,
				   account_id=t_dict['account_id'])