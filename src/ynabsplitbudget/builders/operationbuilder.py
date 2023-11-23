from dataclasses import dataclass
from typing import Optional

from src.ynabsplitbudget.models.charge import Charge, ChargeNew, ChargeNewIncompleteRecipient, ChargeNewIncompleteOwner, ChargeChanged, ChargeOwnerDeleted, ChargeRecipientDeleted
from src.ynabsplitbudget.models.config import Config
from src.ynabsplitbudget.models.operations import Operation, OperationInsert, OperationSplit, OperationDelete, OperationUpdate
from src.ynabsplitbudget.models.user import User


@dataclass
class OperationBuilder:
	user_1: User
	user_2: User

	@classmethod
	def from_config(cls, config: Config):
		return cls(user_1=config.user_1,
				   user_2=config.user_2)

	def from_charge(self, charge: Charge, user: User) -> Optional[Operation]:
		if isinstance(charge, ChargeNew):
			if charge.owner == user:
				return self._build_ynab_split(charge=charge)
			else:
				return self._build_ynab_insert(charge=charge)

		elif isinstance(charge, ChargeNewIncompleteRecipient):
			if charge.owner != user:
				return self._build_ynab_insert(charge=charge)

		elif isinstance(charge, ChargeNewIncompleteOwner):
			if charge.owner == user:
				return self._build_ynab_split(charge=charge)
			else:
				return self._build_ynab_update(charge=charge)

		elif isinstance(charge, ChargeChanged):
			if charge.owner != user:
				return self._build_ynab_update(charge=charge)

		elif isinstance(charge, ChargeOwnerDeleted):
			if charge.owner != user:
				return self._build_ynab_delete(charge=charge)

		elif isinstance(charge, ChargeRecipientDeleted):
			if charge.owner != user:
				return self._build_ynab_insert(charge=charge)

	@staticmethod
	def _build_ynab_insert(charge: [ChargeNew, ChargeNewIncompleteRecipient]) -> OperationInsert:
		return OperationInsert(amount=-charge.owner_owed,
							   date=charge.charge_date,
							   hashed_id=charge.id,
							   memo=charge.memo,
							   payee=charge.payee_name,
							   owner=charge.recipient)

	@staticmethod
	def _build_ynab_split(charge: [ChargeNew, ChargeNewIncompleteOwner]) -> OperationSplit:
		return OperationSplit(paid=charge.paid,
							  owed=charge.owner_owed,
							  memo=charge.memo,
							  payee=charge.payee_name,
							  id=charge.owner_transaction_id,
							  category_id=charge.owner_category.id,
							  owner=charge.owner)

	@staticmethod
	def _build_ynab_delete(charge: ChargeOwnerDeleted) -> OperationDelete:
		return OperationDelete(id=charge.recipient_transaction_id,
							   owner=charge.recipient)

	@staticmethod
	def _build_ynab_update(charge: [ChargeChanged, ChargeNewIncompleteOwner]) -> OperationUpdate:
		return OperationUpdate(id=charge.recipient_transaction_id,
							   amount=-charge.recipient_owed,
							   date=charge.charge_date,
							   memo=charge.memo,
							   payee=charge.payee_name,
							   owner=charge.recipient)

	def _fetch_partner(self, owner: User) -> User:
		return self.user_2 if owner == self.user_1 else self.user_1
