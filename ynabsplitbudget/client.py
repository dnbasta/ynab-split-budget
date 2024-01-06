import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import requests

from ynabsplitbudget.models.splittransaction import SplitTransaction
from ynabsplitbudget.transactionbuilder import TransactionBuilder
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound, SplitNotValid
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
			"amount": - t.amount,
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

		flag_splits = self._filter_none([self._build_transaction(t) for t in transactions_dicts
										 if t['flag_color'] == self.user.flag])

		return flag_splits

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

	@staticmethod
	def _filter_none(li: list) -> list:
		return [i for i in li if i is not None]

	def _build_transaction(self, t_dict: dict) -> Optional[SplitTransaction]:
		try:
			split_amount = self._parse_split(t_dict)
			return SplitTransaction.from_dict(t_dict=t_dict, split_amount=split_amount)
		except SplitNotValid as e:
			print(e)
			return None

	@staticmethod
	def _parse_split(t_dict: dict) -> Optional[float]:
		amount = t_dict['amount']
		rep = f"[{t_dict['date']} | {t_dict['payee_name']} | {amount/1000:.2f} | {t_dict['memo']}]"

		try:
			r = re.search(r'@(\d+\.?\d*)(%?)', t_dict['memo'])
		except TypeError:
			r = None

		# return half the amount if no split attribution is found
		if r is None:
			return amount * 0.5

		split_number = float(r.groups()[0])
		if r.groups()[1] == '%':
			if split_number <= 100:
				return amount * split_number / 100
			raise SplitNotValid(f"Split is above 100% for transaction {rep}")
		if split_number * 1000 > abs(amount):
			raise SplitNotValid(f"Split is above total amount of {amount / 1000:.2f} for transaction {rep}")
		sign = -1 if amount < 0 else 1
		return sign * split_number * 1000


