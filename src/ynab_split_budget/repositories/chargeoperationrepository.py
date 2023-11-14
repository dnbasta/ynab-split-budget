from dataclasses import dataclass
from typing import List

from src.ynab_split_budget.builders.chargebuilder import ChargeBuilder, encrypt
from src.ynab_split_budget.builders.chargeoperationbuilder import ChargeOperationBuilder
from src.ynab_split_budget.models.charge import ChargeOperation
from src.ynab_split_budget.repositories.baserepository import BaseRepository
from src.ynab_split_budget.config import Config, ServerKnowledge, User
from src.ynab_split_budget.repositories.transactionlookuprepository import TransactionLookupRepository


@dataclass
class ChargeOperationRepository:
	charges: List[ChargeOperation]
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

		cob = ChargeOperationBuilder.from_config(config=config, charge_builder=cb)

		# create charges
		user_1_charge_ops = [cob.from_transaction(t) for t in base_repo.user_1_changed]
		user_2_charge_ops = [cob.from_transaction(t) for t in base_repo.user_2_changed]

		charge_ops = [c for c in set(user_1_charge_ops + user_2_charge_ops) if c is not None]

		return cls(charges=charge_ops,
				   server_knowledge=base_repo.server_knowledge,
				   user_1=config.user_1,
				   user_2=config.user_2)

	@property
	def user_1_owned(self) -> int:
		return len([c for c in self.charges if c.charge.owner == self.user_1])

	@property
	def user_2_owned(self) -> int:
		return len([c for c in self.charges if c.charge.owner == self.user_2])
