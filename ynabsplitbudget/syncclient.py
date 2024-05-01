from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Union

import requests
from requests import HTTPError

from ynabsplitbudget.transactionbuilder import TransactionBuilder
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction, ComplementTransaction
from ynabsplitbudget.models.user import User

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


@dataclass
class SyncClient:

	def __init__(self, user: User):
		self.session = requests.Session()
		self.session.headers.update({'Authorization': f'Bearer {user.token}'})
		self.user = user
		self.transaction_builder = TransactionBuilder(user=user)

	def fetch_roots(self, since: date) -> List[RootTransaction]:
		url = f'{YNAB_BASE_URL}budgets/{self.user.budget_id}/accounts/{self.user.account_id}/transactions'
		r = self.session.get(url, params={'since_date': datetime.strftime(since, '%Y-%m-%d')})
		r.raise_for_status()
		transactions_dicts = r.json()['data']['transactions']
		transactions_filtered = [t for t in transactions_dicts if not t['cleared'] == 'uncleared'
							  and t['deleted'] is False
							  and (t['import_id'] is None or 's||' not in t['import_id'])
							  and t['payee_name'] != 'Reconciliation Balance Adjustment']
		transactions = [self.transaction_builder.build_root(t_dict=t) for t in transactions_filtered]
		return transactions

	def fetch_lookup(self, since: date) -> List[Union[RootTransaction, LookupTransaction, ComplementTransaction]]:
		url = f'{YNAB_BASE_URL}budgets/{self.user.budget_id}/transactions'
		r = self.session.get(url, params={'since_date': datetime.strftime(since, '%Y-%m-%d')})
		r.raise_for_status()
		data_dict = r.json()['data']['transactions']
		transactions = [self.transaction_builder.build(t_dict=t) for t in data_dict]
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
		url = f'{YNAB_BASE_URL}budgets/{self.user.budget_id}/transactions'
		data = {'transaction': {
			"account_id": self.user.account_id,
			"date": t.transaction_date.strftime("%Y-%m-%d"),
			"amount": - t.amount,
			"payee_name": t.payee_name,
			"memo": t.memo,
			"cleared": 'cleared',
			"approved": False,
			"import_id": f's||{t.share_id}||{iteration}'
		}}
		r = self.session.post(url, json=data)
		r.raise_for_status()

	def fetch_balance(self) -> int:
		url = f'{YNAB_BASE_URL}budgets/{self.user.budget_id}/accounts/{self.user.account_id}'
		r = self.session.get(url)
		r.raise_for_status()
		balance = r.json()['data']['account']['cleared_balance']
		return balance

	def delete_complement(self, transaction_id: str) -> None:
		url = f'{YNAB_BASE_URL}budgets/{self.user.budget_id}/transactions/{transaction_id}'
		r = self.session.delete(url)
		r.raise_for_status()
