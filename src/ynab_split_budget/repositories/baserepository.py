from dataclasses import dataclass
from typing import List, FrozenSet

from src.ynab_split_budget.client import Client
from src.ynab_split_budget.models.transaction import Transaction
from src.ynab_split_budget.config import Config, ServerKnowledge


@dataclass
class BaseRepository:
	user_1_changed: List[Transaction]
	user_1_lookup: List[Transaction]
	user_2_changed: List[Transaction]
	user_2_lookup: List[Transaction]
	server_knowledge: ServerKnowledge

	@classmethod
	def from_config(cls, config: Config):
		user_client = Client.from_config(user=config.user_1,
										 last_server_knowledge=config.last_server_knowledge.user_1)
		partner_client = Client.from_config(user=config.user_2,
											last_server_knowledge=config.last_server_knowledge.user_2)

		# fetch changed records
		user_changed, user_server_knowledge = user_client.fetch_changed()
		partner_changed, partner_server_knowledge = partner_client.fetch_changed()

		server_knowledge = ServerKnowledge(user_1=user_server_knowledge, user_2=partner_server_knowledge)

		# fetch lookup records
		if len(user_changed + partner_changed) > 0:
			lookup_date = min([t.transaction_date for t in user_changed] + [t.transaction_date for t in partner_changed])
			user_lookup = user_client.fetch_lookup(since=lookup_date)
			partner_lookup = partner_client.fetch_lookup(since=lookup_date)
		else:
			user_lookup = []
			partner_lookup = []

		return BaseRepository(user_1_changed=user_changed,
							  user_2_changed=partner_changed,
							  user_1_lookup=user_lookup,
							  user_2_lookup=partner_lookup,
							  server_knowledge=server_knowledge)

	def fetch_by_transaction_id(self, transaction_id: str) -> Transaction:
		return next((t for t in self.user_1_changed + self.user_1_lookup + self.user_2_lookup + self.user_2_changed
					 if t.id == transaction_id))

	def user_1_transactions(self) -> FrozenSet[Transaction]:
		return frozenset(self.user_1_changed + self.user_1_lookup)

	def user_2_transactions(self) -> FrozenSet[Transaction]:
		return frozenset(self.user_2_changed + self.user_2_lookup)
