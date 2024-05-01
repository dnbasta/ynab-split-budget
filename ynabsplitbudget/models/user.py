from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from ynabsplitbudget.client import Client
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
		client = Client(token=self.token, user_name=self.name, budget_id=self.budget_id, account_id=self.account_id)
		return client.fetch_account(budget_id=self.budget_id, account_id=self.account_id)

	@classmethod
	def from_dict(cls, data: dict) -> 'User':
		"""Creates user object from dict"""
		return cls(name=data['name'], token=data['token'], budget_id=data['budget_id'], account_id=data['account_id'],
				   flag_color=data['flag_color'])

	@classmethod
	def from_yaml(cls, path: str) -> 'User':
		"""Create instance by loading config from YAML file

		:param path: Path to the YAML file

		:returns: instance of YnabSplitBudget class
		"""
		with Path(path).open(mode='r') as f:
			config_dict = yaml.safe_load(f)

		return cls.from_dict(config_dict)
