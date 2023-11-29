import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import requests

from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.transactionbuilder import TransactionBuilder
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.transaction import Transaction, RootTransaction
from ynabsplitbudget.models.user import User

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


class ClientMixin:

	@staticmethod
	def _header(token: str):
		return {'Authorization': f'Bearer {token}'}


class BaseClient(ClientMixin):

	def fetch_account(self, budget_name: str, account_name: str, token: str, user_name: str) -> Account:
		r = requests.get(f'{YNAB_BASE_URL}budgets?include_accounts=true', headers=self._header(token))
		r.raise_for_status()
		r_dict = r.json()

		try:
			budget = next(b for b in r_dict['data']['budgets'] if b['name'] == budget_name)
		except StopIteration:
			raise BudgetNotFound(f"No budget with name '{budget_name} found for {user_name}'")

		try:
			account = next(a for a in budget['accounts'] if a['name'] == account_name and a['deleted'] is False)
			transfer_payee_id = account['transfer_payee_id']
		except StopIteration:
			raise AccountNotFound(f"No Account with name '{account_name}' fund in budget '{budget_name} "
								  f"for user {user_name}'")

		return Account(budget_id=budget['id'],
					   account_id=account['id'],
					   transfer_payee_id=transfer_payee_id,
					   budget_name=budget_name,
					   account_name=account_name,
					   currency=budget['currency_format']['iso_code'])


@dataclass
class SyncClient(BaseClient):
	user: User

	def fetch_new(self) -> List[RootTransaction]:
		url = (f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/accounts/'
			   f'{self.user.account.account_id}/transactions')

		r = requests.get(url, headers=self._header(self.user.token))
		r.raise_for_status()
		data_dict = r.json()['data']

		transactions_dicts = [t for t in data_dict['transactions'] if not t['cleared'] in ('reconciled', 'uncleared')
							  and t['deleted'] is False
							  and (t['import_id'] is None or 's||' not in t['import_id'])]

		stb = TransactionBuilder(self.user)
		transactions = [stb.build_root_transaction(t_dict=t) for t in transactions_dicts]

		return transactions

	def fetch_lookup(self, since: date) -> List[Transaction]:
		params = {'since_date': datetime.strftime(since, '%Y-%m-%d')}
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions'

		r = requests.get(url, params=params, headers=self._header(self.user.token))
		r.raise_for_status()
		data_dict = r.json()['data']

		stb = TransactionBuilder(self.user)
		transactions = [stb.build(t_dict=t) for t in data_dict['transactions']]

		return transactions

	def insert_complement(self, t: RootTransaction):

		data = {'transaction': {
			"account_id": self.user.account.account_id,
			"date": t.transaction_date.strftime("%Y-%m-%d"),
			"amount": - int(t.amount * 1000),
			"payee_name": None if 'Transfer : ' in t.payee_name else t.payee_name,
			"memo": t.memo,
			"cleared": 'cleared',
			"approved": False,
			"import_id": f's||{t.share_id}'
		}}
		r = requests.post(f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions', json=data,
						  headers=self._header(self.user.token))
		r.raise_for_status()


@dataclass
class SplitClient(BaseClient):
	user: User

	def fetch_new_to_split(self) -> List[SplitTransaction]:
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions'

		r = requests.get(url, headers=self._header(self.user.token))
		r.raise_for_status()
		data_dict = r.json()['data']

		transactions_dicts = [t for t in data_dict['transactions'] if not t['cleared'] in ('reconciled', 'uncleared')
							  and t['deleted'] is False and len(t['subtransactions']) == 0]

		flag_splits = self._filter_none([self._create_for_flag(t) for t in transactions_dicts
										 if t['flag_color'] is not None])
		category_splits = self._filter_none([self._create_for_category(t) for t in transactions_dicts
						   if t['id'] not in [tf.id for tf in flag_splits]])

		return flag_splits + category_splits

	def insert_split(self, t: SplitTransaction):
		amount = int(t.amount * 1000)
		data = {'transaction': {
			"subtransactions": [{"amount": int(amount / 2),
								 "payee_id": self.user.account.transfer_payee_id,
								 "memo": t.memo,
								 "cleared": "cleared"
								},
								{"amount": int(amount / 2),
								 "category_id": t.category.id,
								 "cleared": "cleared"
								 }]
		}}
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions/{t.id}'

		r = requests.put(url, json=data, headers=self._header(self.user.token))
		r.raise_for_status()

	def _create_for_flag(self, t_dict: dict) -> SplitTransaction:
		for f in self.user.flag_splits:
			if f.color == t_dict['flag_color']:
				return SplitTransaction.from_dict(t_dict=t_dict, split=f.split)

	def _create_for_category(self, t_dict: dict) -> SplitTransaction:
		for f in self.user.category_splits:
			if f.name == self._remove_emojis(t_dict['category_name']):
				return SplitTransaction.from_dict(t_dict=t_dict, split=f.split)

	@staticmethod
	def _remove_emojis(text: str) -> str:
		emoji = re.compile("["
						  u"\U0001F600-\U0001F64F"  # emoticons
						  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
						  u"\U0001F680-\U0001F6FF"  # transport & map symbols
						  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
						  u"\U00002500-\U00002BEF"  # chinese char
						  u"\U00002702-\U000027B0"
						  u"\U00002702-\U000027B0"
						  u"\U000024C2-\U0001F251"
						  u"\U0001f926-\U0001f937"
						  u"\U00010000-\U0010ffff"
						  u"\u2640-\u2642"
						  u"\u2600-\u2B55"
						  u"\u200d"
						  u"\u23cf"
						  u"\u23e9"
						  u"\u231a"
						  u"\ufe0f"  # dingbats
						  u"\u3030"
						  "]+", re.UNICODE)
		return re.sub(emoji, '', text).lstrip().rstrip()

	@staticmethod
	def _filter_none(li: list) -> list:
		return [i for i in li if i is not None]
