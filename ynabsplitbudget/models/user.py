from dataclasses import dataclass
from typing import Literal

from ynabsplitbudget.baseclient import BaseClient
from ynabsplitbudget.models.account import Account


@dataclass(eq=True, frozen=True)
class User:
	"""Object representing a user.

	:ivar name: The name of the user.
	:ivar token: The token for access to the YNAB API.
	:ivar budget_id: The ID of the YNAB budget to use.
	:ivar account_id: The ID of the split account to use in the budget.
	:ivar flag_color: The color of the flag with which split transactions are marked
	"""
	name: str
	token: str
	budget_id: str
	account_id: str
	flag_color: Literal['red', 'green', 'blue', 'orange', 'purple', 'yellow']

	def fetch_account(self) -> Account:
		"""Fetches account data from the API or user

		:return: Account object with budget and account name, transfer_payee_id and currency
		"""
		client = BaseClient(token=self.token, user_name=self.name)
		return client.fetch_account(budget_id=self.budget_id, account_id=self.account_id)

	@classmethod
	def from_dict(cls, data: dict) -> 'User':
		"""Creates user object from dict"""
		return cls(name=data['name'], token=data['token'], budget_id=data['budget_id'], account_id=data['account_id'],
				   flag_color=data['flag_color'])
