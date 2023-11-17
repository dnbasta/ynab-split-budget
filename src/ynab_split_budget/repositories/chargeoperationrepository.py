from dataclasses import dataclass
from typing import List

from src.ynab_split_budget.builders.chargebuilder import ChargeBuilder, encrypt
from src.ynab_split_budget.builders.operationbuilder import OperationBuilder
from src.ynab_split_budget.models.charge import Charge
from src.ynab_split_budget.models.operations import Operation
from src.ynab_split_budget.repositories.baserepository import BaseRepository
from src.ynab_split_budget.config import Config, ServerKnowledge, User
from src.ynab_split_budget.repositories.transactionlookuprepository import TransactionLookupRepository


@dataclass
class ChargeOperationRepository:
	charges: List[Charge]
	user_1_operations: List[Operation]
	user_2_operations: List[Operation]
	server_knowledge: ServerKnowledge
	user_1: User
	user_2: User

	@classmethod
	def from_config(cls, base_repo: BaseRepository, config: Config):

		# create ChargeBuilder
		user_1_lookup_repo = TransactionLookupRepository(entries=base_repo.user_1_transactions(),
														 encrypt_function=encrypt)
		user_2_lookup_repo = TransactionLookupRepository(entries=base_repo.user_2_transactions(),
														 encrypt_function=encrypt)

		cb = ChargeBuilder(user_2_lookup=user_2_lookup_repo,
						   user_1_lookup=user_1_lookup_repo,
						   user_1=config.user_1,
						   user_2=config.user_2)

		user_1_charges = [cb.from_transaction(t) for t in base_repo.user_1_changed]
		user_2_charges = [cb.from_transaction(t) for t in base_repo.user_2_changed]

		charges = [c for c in set(user_1_charges + user_2_charges) if c is not None]

		# create operations
		ob = OperationBuilder.from_config(config=config)
		user_1_ops = [ob.from_charge(charge=c, user=config.user_1) for c in charges]
		user_2_ops = [ob.from_charge(charge=c, user=config.user_2) for c in charges]

		return cls(charges=charges,
				   user_1_operations=user_1_ops,
				   user_2_operations=user_2_ops,
				   server_knowledge=base_repo.server_knowledge,
				   user_1=config.user_1,
				   user_2=config.user_2)

	@property
	def user_1_charges(self) -> List[Charge]:
		return [c for c in self.charges if c.owner == self.user_1]

	@property
	def user_2_charges(self) -> List[Charge]:
		return [c for c in self.charges if c.owner == self.user_2]

	@property
	def user_1_ops(self):
		return [o for o in self.user_1_operations if o is not None]

	@property
	def user_2_ops(self):
		return [o for o in self.user_2_operations if o is not None]