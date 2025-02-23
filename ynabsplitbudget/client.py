from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Union

from requests import HTTPError, Session

from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.transactionbuilder import TransactionBuilder
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction, ComplementTransaction

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


@dataclass
class Client:

	def __init__(self, user_name: str, budget_id: str, account_id: str, session: Session):
		self.session = session
		self.user_name = user_name
		self.budget_id = budget_id
		self.account_id = account_id
		self.transaction_builder = TransactionBuilder(account_id=self.account_id)

	def fetch_account(self, budget_id: str, account_id: str) -> Account:
		r = self.session.get(f'{YNAB_BASE_URL}budgets', params=dict(include_accounts=True))
		r.raise_for_status()
		data_dict = r.json()['data']

		try:
			budget = next(b for b in data_dict['budgets'] if b['id'] == budget_id)
		except StopIteration:
			raise BudgetNotFound(f"No budget with id '{budget_id} found for {self.user_name}'")

		try:
			account = next(a for a in budget['accounts'] if a['id'] == account_id and a['deleted'] is False)
		except StopIteration:
			raise AccountNotFound(f"No Account with id '{account_id}' fund in budget '{budget['name']} "
								  f"for user {self.user_name}'")

		return Account(budget_id=budget_id,
					   budget_name=budget['name'],
					   account_id=account_id,
					   account_name=account['name'],
					   transfer_payee_id=account['transfer_payee_id'],
					   currency=budget['currency_format']['iso_code'])

	def fetch_roots(self, since: date, include_uncleared: bool) -> List[RootTransaction]:
		url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/accounts/{self.account_id}/transactions'
		r = self.session.get(url, params={'since_date': datetime.strftime(since, '%Y-%m-%d')})
		r.raise_for_status()
		transactions_dicts = r.json()['data']['transactions']
		transactions_filtered = [t for t in transactions_dicts if t['deleted'] is False
							  and (t['import_id'] is None or 's||' not in t['import_id'])
							  and t['payee_name'] != 'Reconciliation Balance Adjustment']
		if not include_uncleared:
			transactions_filtered = [t for t in transactions_filtered  if not t['cleared'] == 'uncleared']
		transactions = [self.transaction_builder.build_root(t_dict=t) for t in transactions_filtered]
		return transactions

	def fetch_lookup(self, since: date) -> List[Union[RootTransaction, LookupTransaction, ComplementTransaction]]:
		url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/transactions'
		r = self.session.get(url, params={'since_date': datetime.strftime(since, '%Y-%m-%d')})
		r.raise_for_status()
		data_dict = r.json()['data']['transactions']
		transactions = [self.transaction_builder.build(t_dict=t) for t in data_dict]
		return transactions

	def insert_complement(self, t: RootTransaction) -> ComplementTransaction:
		iteration = 0
		while True:
			try:
				return self._insert(t, iteration=iteration)
			except HTTPError as e:
				if e.response.status_code == 409:
					iteration += 1

	def _insert(self, t: RootTransaction, iteration: int) -> ComplementTransaction:
		url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/transactions'
		data = {'transaction': {
			"account_id": self.account_id,
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
		complement = self.transaction_builder.build_complement(r.json()['data']['transaction'])
		return complement

	def fetch_balance(self) -> int:
		url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/accounts/{self.account_id}'
		r = self.session.get(url)
		r.raise_for_status()
		balance = r.json()['data']['account']['cleared_balance']
		return balance

	def delete_complement(self, transaction_id: str) -> None:
		url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/transactions/{transaction_id}'
		r = self.session.delete(url)
		r.raise_for_status()
