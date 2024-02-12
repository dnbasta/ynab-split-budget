from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import requests

from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.transactionbuilder import TransactionBuilder, SplitTransactionBuilder
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

	def __init__(self, token: str, user_name: str):
		self._token = token
		self._user_name = user_name

	def fetch_account(self, budget_id: str, account_id: str) -> Account:
		r = requests.get(f'{YNAB_BASE_URL}budgets?include_accounts=true', headers=self._header(self._token))
		r.raise_for_status()
		data_dict = r.json()['data']

		try:
			budget = next(b for b in data_dict['budgets'] if b['id'] == budget_id)
		except StopIteration:
			raise BudgetNotFound(f"No budget with id '{budget_id} found for {self._user_name}'")

		try:
			account = next(a for a in budget['accounts'] if a['id'] == account_id and a['deleted'] is False)
		except StopIteration:
			raise AccountNotFound(f"No Account with id '{account_id}' fund in budget '{budget['name']} "
								  f"for user {self._user_name}'")

		return Account(budget_id=budget_id,
					   budget_name=budget['name'],
					   account_id=account_id,
					   account_name=account['name'],
					   transfer_payee_id=account['transfer_payee_id'],
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
			"amount": - t.amount,
			"payee_name": t.payee_name,
			"memo": t.memo,
			"cleared": 'cleared',
			"approved": False,
			"import_id": f's||{t.share_id}'
		}}
		r = requests.post(f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions', json=data,
						  headers=self._header(self.user.token))
		r.raise_for_status()

	def fetch_balance(self) -> int:
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/accounts/{self.user.account.account_id}'
		r = requests.get(url, headers=self._header(self.user.token))
		r.raise_for_status()
		return r.json()['data']['account']['cleared_balance']


@dataclass
class SplitClient(BaseClient):
	user: User

	def fetch_new_to_split(self) -> List[SplitTransaction]:
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions'

		r = requests.get(url, headers=self._header(self.user.token))
		r.raise_for_status()
		data_dict = r.json()['data']

		transactions_dicts = [t for t in data_dict['transactions'] if not t['cleared'] == 'uncleared'
							  and t['deleted'] is False and len(t['subtransactions']) == 0]
		stb = SplitTransactionBuilder()
		flag_splits = [stb.build(t) for t in transactions_dicts if t['flag_color'] == self.user.flag]

		return [s for s in flag_splits if s is not None]

	def insert_split(self, t: SplitTransaction):
		data = {'transaction': {
			"subtransactions": [{"amount": int(t.split_amount),
								 "payee_id": self.user.account.transfer_payee_id,
								 "memo": t.memo,
								 "cleared": "cleared"
								},
								{"amount": int(t.amount - t.split_amount),
								 "category_id": t.category.id,
								 "cleared": "cleared"
								 }]
		}}
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions/{t.id}'

		r = requests.put(url, json=data, headers=self._header(self.user.token))
		r.raise_for_status()
