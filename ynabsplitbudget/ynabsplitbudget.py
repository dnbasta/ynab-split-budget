from pathlib import Path
from typing import List

import yaml

from ynabsplitbudget.client import BaseClient, SyncClient
from ynabsplitbudget.models.categorysplit import CategorySplit
from ynabsplitbudget.models.config import Config
from ynabsplitbudget.models.flagsplit import FlagSplit
from ynabsplitbudget.models.response import Response, ResponseItem
from ynabsplitbudget.models.user import User
from ynabsplitbudget.transactionrepository import TransactionRepository


class YnabSplitBudget:
	def __init__(self, path: str):
		with Path(path).open(mode='r') as f:
			config_dict = yaml.safe_load(f)
		self._config = Config(user_1=self._load_user(config_dict['user_1']),
							  user_2=self._load_user(config_dict['user_2']))

	def _load_user(self, user_dict: dict) -> User:
		account = BaseClient().fetch_account(budget_name=user_dict['budget'],
										  account_name=user_dict['account'],
										  user_name=user_dict['name'],
										  token=user_dict['token'])

		cat_splits = self._load_category_splits(user_dict['categories']) if 'categories' in user_dict.keys() else []
		flag_splits = self._load_flag_splits(user_dict['flags']) if 'flags' in user_dict.keys() else []
		return User(name=user_dict['name'], token=user_dict['token'], account=account,
					category_splits=cat_splits,
					flag_splits=flag_splits)

	@staticmethod
	def _load_category_splits(categories: List[dict]) -> List[CategorySplit]:
		return [CategorySplit(name=c['name'], split=c['split']) for c in categories]

	@staticmethod
	def _load_flag_splits(flags: List[dict]) -> List[FlagSplit]:
		return [FlagSplit(color=c['color'], split=c['split']) for c in flags]


	def fetch_new(self) -> Response:
		st_repo = TransactionRepository(self._config).populate()
		print(f'fetched new: {self._config.user_1.name}: {len(st_repo.user_1)} '
			  f'{self._config.user_2.name}: {len(st_repo.user_2)}')
		return Response(user_1=ResponseItem(name=self._config.user_1.name,
												   transactions=st_repo.user_1),
						user_2=ResponseItem(name=self._config.user_2.name,
												   transactions=st_repo.user_2))

	def insert_complement(self, response: Response):
		u1c = SyncClient(user=self._config.user_1)
		u2c = SyncClient(user=self._config.user_2)

		[u1c.insert_complement(t) for t in response.user_2.transactions]
		[u2c.insert_complement(t) for t in response.user_1.transactions]
		print(f'inserted complements: {self._config.user_1.name}: {len(response.user_2.transactions)} '
			  f'{self._config.user_2.name}: {len(response.user_1.transactions)}')
