from dataclasses import dataclass
from typing import Union

import yaml

from src.ynabsplitbudget.client import BaseClient
from src.ynabsplitbudget.models.account import BaseAccount, Account
from src.ynabsplitbudget.models.config import Config, ConfigMissingKnowledge
from src.ynabsplitbudget.models.user import User


@dataclass
class ConfigBuilder:
	path: str

	def build_from_path(self) -> Union[Config, ConfigMissingKnowledge]:
		with open(f'{self.path}', 'r') as f:
			config_dict = yaml.safe_load(f)
		user_1 = self._build_user(config_dict['user_1'])
		user_2 = self._build_user(config_dict['user_2'])
		if not all(isinstance(a, Account) for a in [user_1.account, user_2.account]):
			return ConfigMissingKnowledge(user_1=user_1, user_2=user_2, path=self.path)
		return Config(user_1=user_1, user_2=user_2, path=self.path)

	def build_from_config(self, config: (Config, ConfigMissingKnowledge),
						  user_1_server_knowledge: int, user_2_server_knowledge: int) -> Config:

		user_1 = self._build_user_from_user(user=config.user_1, server_knowledge=user_1_server_knowledge)
		user_2 = self._build_user_from_user(user=config.user_2, server_knowledge=user_2_server_knowledge)
		return Config(user_1=user_1,
				   	  user_2=user_2,
					  path=self.path)

	def _build_user(self, user_dict: dict) -> User:
		account = self._build_account_from_path(user_dict)
		return User(name=user_dict['name'],
					token=user_dict['token'],
					account=account)

	def _build_account_from_path(self, user_dict: dict) -> Union[BaseAccount, Account]:
		base_account = self._fetch_base_account(user_dict)
		if 'server_knowledge' in user_dict.keys():
			return Account.from_base_account(base_account, server_knowledge=user_dict['server_knowledge'])
		else:
			return base_account

	def _build_user_from_user(self, user: User, server_knowledge: int) -> User:
		return User(name=user.name,
					token=user.token,
					account=self._build_account_from_account(account=user.account, server_knowledge=server_knowledge))

	@staticmethod
	def _build_account_from_account(account: Account, server_knowledge: int) -> Account:
		return Account(budget_id=account.budget_id,
					   account_id=account.account_id,
					   transfer_payee_id=account.transfer_payee_id,
					   server_knowledge=server_knowledge,
					   account_name=account.account_name,
					   budget_name=account.budget_name,
					   currency=account.currency)

	@staticmethod
	def _fetch_base_account(user_dict: dict) -> BaseAccount:
		client = BaseClient(token=user_dict['token'])
		return client.fetch_account(budget_name=user_dict['budget'],
									account_name=user_dict['account'],
									user_name=user_dict['name'])
