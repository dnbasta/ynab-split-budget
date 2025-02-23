from datetime import date
from typing import List

from ynabtransactionadjuster import Adjuster, Credentials, ModifierSubTransaction
from ynabtransactionadjuster.models import Transaction, Modifier

from session import Session
from ynabsplitbudget.splitparser import SplitParser


class ReconcileAdjuster(Adjuster):

	def filter(self, transactions: List[Transaction]) -> List[Transaction]:
		return [t for t in transactions if t.cleared == 'cleared']

	def adjust(self, original: Transaction, modifier: Modifier) -> Modifier:
		modifier.cleared = 'reconciled'
		if not modifier.category:
			modifier.category = self.categories.fetch_by_name('Inflow: Ready to Assign')
		return modifier


class ClearAdjuster(Adjuster):

	def __init__(self, credentials: Credentials, split_transaction_ids: List[str], session: Session):
		super().__init__(credentials=credentials, session=session)
		self.split_transaction_ids = split_transaction_ids

	def filter(self, transactions: List[Transaction]) -> List[Transaction]:
		return [t for t in transactions
					 	if t.cleared == 'uncleared'
						and t.id in self.split_transaction_ids]

	def adjust(self, original: Transaction, modifier: Modifier) -> Modifier:
		modifier.cleared = 'cleared'
		if not modifier.category:
			modifier.category = self.categories.fetch_by_name('Inflow: Ready to Assign')
		return modifier


class SplitAdjuster(Adjuster):

	def __init__(self, credentials: Credentials, flag_color: str, transfer_payee_id: str, account_id: str, since: date,
				 session: Session):
		super().__init__(credentials=credentials, session=session)
		self.flag_color = flag_color
		self.transfer_payee_id = transfer_payee_id
		self.account_id = account_id
		self.since = since

	def filter(self, transactions: List[Transaction]) -> List[Transaction]:
		return [t for t in transactions if t.cleared in ('cleared', 'reconciled')
				and t.approved
				and t.flag_color == self.flag_color
				and not t.subtransactions
				and not t.account.id == self.account_id
				and t.transaction_date >= self.since]

	def adjust(self, original: Transaction, modifier: Modifier) -> Modifier:
		split_amount = SplitParser().parse_split(transaction=original)
		s1 = ModifierSubTransaction(amount=split_amount, payee=self.payees.fetch_by_id(self.transfer_payee_id),
									memo=f"{original.payee.name} | {original.memo}")
		s2 = ModifierSubTransaction(amount=original.amount - split_amount, category=original.category, memo=original.memo)
		modifier.subtransactions = [s1, s2]
		return modifier
