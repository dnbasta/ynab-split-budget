from dataclasses import dataclass
from datetime import date, datetime


@dataclass(eq=True, frozen=True)
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
				   amount=-round(float(t_dict['amount']) / 1000, 2),
				   account_id=t_dict['account_id'],
				   share_id=share_id)


@dataclass(eq=True, frozen=True)
class RootTransaction(Transaction):
	pass


@dataclass(eq=True, frozen=True)
class ComplementTransaction(Transaction):
	pass
