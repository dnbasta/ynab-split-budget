from dataclasses import dataclass

from src.ynab_split_budget.builders.chargebuilder import ChargeBuilder
from src.ynab_split_budget.builders.operationbuilder import OperationBuilder
from src.ynab_split_budget.models.charge import ChargeOperation
from src.ynab_split_budget.config import Config, User
from src.ynab_split_budget.models.transaction import Transaction


@dataclass
class ChargeOperationBuilder:
	user_1: User
	user_2: User
	charge_builder: ChargeBuilder
	operation_builder: OperationBuilder

	@classmethod
	def from_config(cls, config: Config, charge_builder: ChargeBuilder):
		return cls(user_1=config.user_1,
				   user_2=config.user_2,
				   charge_builder=charge_builder,
				   operation_builder=OperationBuilder.from_config(config))

	def from_transaction(self, transaction: Transaction) -> ChargeOperation:
		charge = self.charge_builder.from_transaction(transaction)
		if charge is not None:
			return ChargeOperation(charge=charge,
							   	   user_1_operation=self.operation_builder.op_from_charge(charge=charge,
																						  user=self.user_1),
							   	   user_2_operation=self.operation_builder.op_from_charge(charge=charge,
																						  user=self.user_2))
