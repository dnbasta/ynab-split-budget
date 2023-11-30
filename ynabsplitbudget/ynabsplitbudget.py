from pathlib import Path
from typing import List

import yaml

from ynabsplitbudget.client import BaseClient, SyncClient, SplitClient
from ynabsplitbudget.models.categorysplit import CategorySplit
from ynabsplitbudget.models.config import Config
from ynabsplitbudget.models.flagsplit import FlagSplit
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

	def _fetch_user(self, user_name: str):
		return next(u for u in (self._config.user_1, self._config.user_2) if u.name == user_name)

	def insert_complements(self, user_name: str) -> int:
		user = self._fetch_user(user_name)
		partner = self._config.user_1 if user == self._config.user_2 else self._config.user_2
		st_repo = TransactionRepository(user=user, partner=partner).populate()
		c = SyncClient(partner)

		[c.insert_complement(t) for t in st_repo.transactions]
		print(f'inserted {len(st_repo.transactions)} complements into account from {partner.name}')
		return len(st_repo.transactions)

	def split_transactions(self, user_name: str) -> int:
		c = SplitClient(self._fetch_user(user_name))
		st_list = c.fetch_new_to_split()
		[c.insert_split(st) for st in st_list]
		print(f'split {len(st_list)} transactions for {user_name}')
		return len(st_list)