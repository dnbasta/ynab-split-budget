from pathlib import Path

import yaml

from ynabsplitaccount.client import BaseClient, TransactionClient
from ynabsplitaccount.models.config import Config
from ynabsplitaccount.models.response import Response, ResponseItem
from ynabsplitaccount.models.user import User
from ynabsplitaccount.transactionrepository import TransactionRepository


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

	def fetch_new(self) -> Response:
		st_repo = TransactionRepository(self._config).populate()
		print(f'fetched new: {self._config.user_1.name}: {len(st_repo.user_1)} '
			  f'{self._config.user_2.name}: {len(st_repo.user_2)}')
		return Response(user_1=ResponseItem(name=self._config.user_1.name,
												   transactions=st_repo.user_1),
						user_2=ResponseItem(name=self._config.user_2.name,
												   transactions=st_repo.user_2))

	def insert_complement(self, response: Response):
		u1c = TransactionClient(user=self._config.user_1)
		u2c = TransactionClient(user=self._config.user_2)

		[u1c.insert_child(t) for t in response.user_2.transactions]
		[u2c.insert_child(t) for t in response.user_1.transactions]
		print(f'inserted complements: {self._config.user_1.name}: {len(response.user_2.transactions)} '
			  f'{self._config.user_2.name}: {len(response.user_1.transactions)}')
