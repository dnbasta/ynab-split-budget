from dataclasses import dataclass
from datetime import date, datetime

from ynabsplitbudget.models.category import Category


@dataclass(eq=True, frozen=True)
class SplitTransaction:
	id: str
	transaction_date: date
	memo: str
	payee_name: str
	payee_id: str
	category: Category
	amount: float
	split_amount: float
	account_id: str

	@classmethod
	def from_dict(cls, t_dict: dict, split_amount: float):
		return cls(id=t_dict['id'],
				   transaction_date=datetime.strptime(t_dict['date'], '%Y-%m-%d').date(),
				   payee_name=t_dict['payee_name'],
				   memo=t_dict['memo'],
				   amount=t_dict['amount'],
				   payee_id=t_dict['payee_id'],
				   category=Category(name=t_dict['category_name'], id=t_dict['category_id']),
				   split_amount=split_amount,
				   account_id=t_dict['account_id'])
