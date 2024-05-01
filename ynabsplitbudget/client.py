from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Union

import requests
from requests import HTTPError

from ynabsplitbudget.transactionbuilder import TransactionBuilder
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction, ComplementTransaction
from ynabsplitbudget.models.user import User

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


class ClientMixin:
	_token: str

	def _header(self):
		return {'Authorization': f'Bearer {self._token}'}

	def _get(self, url: str, params: dict = None) -> dict:
		r = requests.get(url, params=params, headers=self._header())
		r.raise_for_status()
		return r.json()['data']


@dataclass
class SyncClient(ClientMixin):

	def __init__(self, user: User):
		self._token = user.token
		self.user = user
		self.transaction_builder = TransactionBuilder(user=user)

	def fetch_roots(self, since: date) -> List[RootTransaction]:
		url = (f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/accounts/'
			   f'{self.user.account.account_id}/transactions')

		transactions_dicts = self._get(url, params={'since_date': datetime.strftime(since, '%Y-%m-%d')})['transactions']
		transactions_filtered = [t for t in transactions_dicts if not t['cleared'] == 'uncleared'
							  and t['deleted'] is False
							  and (t['import_id'] is None or 's||' not in t['import_id'])
							  and t['payee_name'] != 'Reconciliation Balance Adjustment']
		transactions = [self.transaction_builder.build_root(t_dict=t) for t in transactions_filtered]
		return transactions

	def fetch_lookup(self, since: date) -> List[Union[RootTransaction, LookupTransaction, ComplementTransaction]]:
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions'
		data_dict = self._get(url, params={'since_date': datetime.strftime(since, '%Y-%m-%d')})
		transactions = [self.transaction_builder.build(t_dict=t) for t in data_dict['transactions']]
		return transactions

	def insert_complement(self, t: RootTransaction):
		iteration = 0
		try_again = True
		while try_again:
			try:
				self._insert(t, iteration=iteration)
				try_again = False
			except HTTPError as e:
				if e.response.status_code == 409:
					iteration += 1

	def _insert(self, t: RootTransaction, iteration: int):
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions'
		data = {'transaction': {
			"account_id": self.user.account.account_id,
			"date": t.transaction_date.strftime("%Y-%m-%d"),
			"amount": - t.amount,
			"payee_name": t.payee_name,
			"memo": t.memo,
			"cleared": 'cleared',
			"approved": False,
			"import_id": f's||{t.share_id}||{iteration}'
		}}
		r = requests.post(url, json=data, headers=self._header())
		r.raise_for_status()

	def fetch_balance(self) -> int:
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/accounts/{self.user.account.account_id}'
		data_dict = self._get(url)
		return data_dict['account']['cleared_balance']

	def delete_complement(self, transaction_id: str) -> None:
		url = f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions/{transaction_id}'
		r = requests.delete(url, headers=self._header())
		r.raise_for_status()
