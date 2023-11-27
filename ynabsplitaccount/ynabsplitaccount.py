from pathlib import Path

import yaml

from ynabsplitaccount.client import BaseClient, ShareTransactionClient
from ynabsplitaccount.models.config import Config
from ynabsplitaccount.models.toshareresponse import ToShareResponse, ToShareResponseItem
from ynabsplitaccount.models.user import User
from ynabsplitaccount.repositories.sharetransactionrepository import ShareTransactionRepository


class YnabSplitAccount:
	def __init__(self, path: str):
		with Path(path).open(mode='r') as f:
			config_dict = yaml.safe_load(f)
		self._config = Config(user_1=self._load_user(config_dict['user_1']),
							  user_2=self._load_user(config_dict['user_2']))

	@staticmethod
	def _load_user(user_dict: dict) -> User:
		account = BaseClient().fetch_account(budget_name=user_dict['budget'],
										  account_name=user_dict['account'],
										  user_name=user_dict['name'],
										  token=user_dict['token'])
		return User(name=user_dict['name'], token=user_dict['token'], account=account)

	def fetch_share_transactions(self) -> ToShareResponse:
		strepo = ShareTransactionRepository.from_config(self._config)
		return ToShareResponse(user_1=ToShareResponseItem(name=self._config.user_1.name,
												   transactions=strepo.fetch_new_user_1()),
							   user_2=ToShareResponseItem(name=self._config.user_2.name,
												   transactions=strepo.fetch_new_user_2()))

	def insert_share_transactions(self, response: ToShareResponse):
		u1c = ShareTransactionClient(user=self._config.user_1)
		u2c = ShareTransactionClient(user=self._config.user_2)

		[u1c.insert_child(t) for t in response.user_2.transactions]
		[u2c.insert_child(t) for t in response.user_1.transactions]
