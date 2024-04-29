from typing import List

from ynabtransactionadjuster import Adjuster, Credentials, ModifierSubTransaction
from ynabtransactionadjuster.models import Transaction, Modifier

from ynabsplitbudget.splitparser import SplitParser


class ReconcileAdjuster(Adjuster):

	def filter(self, transactions: List[Transaction]) -> List[Transaction]:
		return [t for t in transactions if t.cleared == 'cleared']

	def adjust(self, original: Transaction, modifier: Modifier) -> Modifier:
		modifier.cleared = 'reconciled'
		modifier.category = self.categories.fetch_by_name('Inflow: Ready to Assign')
		return modifier


class ClearAdjuster(Adjuster):

	def __init__(self, credentials: Credentials, flag_color: str):
		super().__init__(credentials=credentials)
		self.flag_color = flag_color

	def filter(self, transactions: List[Transaction]) -> List[Transaction]:
		return [t for t in transactions
					 	if t.cleared == 'uncleared'
						and t.transfer_transaction_id
						and self.fetch_transaction(t.transfer_transaction_id).flag_color == self.flag_color]

	def adjust(self, original: Transaction, modifier: Modifier) -> Modifier:
		modifier.cleared = 'cleared'
		modifier.category = self.categories.fetch_by_name('Inflow: Ready to Assign')
		return modifier


class SplitAdjuster(Adjuster):

	def __init__(self, credentials: Credentials, flag_color: str, transfer_payee_id: str):
		super().__init__(credentials=credentials)
		self.flag_color = flag_color
		self.transfer_payee_id = transfer_payee_id

	def filter(self, transactions: List[Transaction]) -> List[Transaction]:
		return [t for t in transactions if t.cleared == 'cleared' and t.flag_color == self.flag_color]

	def adjust(self, original: Transaction, modifier: Modifier) -> Modifier:
		split_amount = SplitParser().parse_split(transaction=original)
		s1 = ModifierSubTransaction(amount=split_amount, payee=self.payees.fetch_by_id(self.transfer_payee_id),
									memo=f"{original.payee.name} | {original.memo}")
		s2 = ModifierSubTransaction(amount=original.amount - split_amount, category=original.category, memo=original.memo)
		modifier.subtransactions = [s1, s2]
		return modifier
