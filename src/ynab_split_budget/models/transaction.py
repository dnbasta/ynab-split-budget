from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.ynab_split_budget.config import User


@dataclass(eq=True, frozen=True)
class Category:
	id: str
	name: str


@dataclass(eq=True, frozen=True)
class Transaction:
	id: str
	transaction_date: date
	memo: str
	payee_name: str
	import_id: str
	deleted: bool
	payee_id: str
	category: Optional[Category]
	owner: User


@dataclass(eq=True, frozen=True)
class TransactionOwed(Transaction):
	owed: float


@dataclass(eq=True, frozen=True)
class TransactionReference(Transaction):
	amount: float


@dataclass(eq=True, frozen=True)
class TransactionPaid(Transaction):
	paid: float


@dataclass(eq=True, frozen=True)
class TransactionPaidToSplit(TransactionPaid):
	pass


@dataclass(eq=True, frozen=True)
class TransactionPaidTransfer(TransactionPaid):
	owed: float = 0


@dataclass(eq=True, frozen=True)
class TransactionPaidDeleted(TransactionPaid):
	pass


@dataclass(eq=True, frozen=True)
class TransactionPaidSplit(TransactionPaid):
	owed: float
	transfer_transaction_id: str
	subtransaction_id_transfer: str
	subtransaction_id_owed: str


@dataclass(eq=True, frozen=True)
class TransactionPaidSplitPart(TransactionPaid):
	pass
