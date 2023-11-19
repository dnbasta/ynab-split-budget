from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, FrozenSet, Union, Callable

from src.ynabsplitbudget.models.transaction import Transaction, TransactionPaid, TransactionOwed, TransactionPaidSplit, TransactionReference


@dataclass(eq=True, frozen=True)
class TransactionLookupRepository:
	entries: FrozenSet[Transaction]
	encrypt_function: Callable

	def fetch_owner_by_hashed_id(self, hashed_id: str) -> Optional[Union[TransactionPaid, TransactionReference]]:
		transaction = next((t for t in self.entries if self.encrypt_function(t.id) == hashed_id), None)
		return transaction

	def fetch_recipient_by_hashed_id(self, hashed_id: str) -> Optional[Union[TransactionOwed, TransactionReference]]:
		transaction = next((t for t in self.entries if t.import_id is not None and hashed_id in t.import_id), None)
		return transaction

	def fetch_parent_by_transfer_transaction_id(self, transfer_transaction_id: str) -> Optional[TransactionPaidSplit]:
		transaction = next((t for t in self.entries
							if isinstance(t, TransactionPaidSplit)
							and t.transfer_transaction_id == transfer_transaction_id), None)
		return transaction

	def oldest_change(self) -> date:
		if len(self.entries) > 0:
			min_date: date = min([t.transaction_date for t in self.entries])
			return min_date
		return (datetime.now() + timedelta(days=1)).date()
