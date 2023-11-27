import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import requests
from requests import Response

from ynabsplitaccount.builders.sharetransactionbuilder import ShareTransactionBuilder
from ynabsplitaccount.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitaccount.models.account import BaseAccount
from ynabsplitaccount.models.sharetransaction import ShareTransaction, ShareTransactionParent
from ynabsplitaccount.models.user import User

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


class ClientMixin:

	@staticmethod
	def _check_response(response: Response):
		r = response.json()
		if 'errors' in r.keys() and len(r['errors']) > 0:
			response.reason = r['errors']['base'][0]
			response.status_code = 400
		try:
			response.raise_for_status()
		except Exception as e:
			print(response.request.path_url)
			print(urllib.parse.unquote(response.request.body))
			raise e

	@staticmethod
	def _header(token: str):
		return {'Authorization': f'Bearer {token}'}


class BaseClient(ClientMixin):

	def fetch_account(self, budget_name: str, account_name: str, token: str, user_name: str) -> BaseAccount:
		r = requests.get(f'{YNAB_BASE_URL}budgets?include_accounts=true', headers=self._header(token))
		self._check_response(r)
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

		return BaseAccount(budget_id=budget['id'],
						   account_id=account['id'],
						   transfer_payee_id=transfer_payee_id,
						   budget_name=budget_name,
						   account_name=account_name,
						   currency=budget['currency_format']['iso_code'])


@dataclass
class ShareTransactionClient(BaseClient):
	user: User

	def fetch_changed(self) -> (List[ShareTransaction], int):
		url = (f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/accounts/'
			   f'{self.user.account.account_id}/transactions')

		r = requests.get(url, headers=self._header(self.user.token))
		r.raise_for_status()
		data_dict = r.json()['data']

		transactions_dicts = [t for t in data_dict['transactions'] if not t['cleared'] in ('reconciled', 'uncleared')
							  and t['deleted'] is False
							  and (t['import_id'] is None or 's||' not in t['import_id'])]

		server_knowledge = data_dict['server_knowledge']
		return self._build_transactions(transactions_dicts), server_knowledge

	def fetch_lookup(self, since: date) -> List[ShareTransaction]:
		params = {'since_date': datetime.strftime(since, '%Y-%m-%d')}
		url = (f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/accounts/'
			   f'{self.user.account.account_id}/transactions')

		r = requests.get(url, params=params, headers=self._header(self.user.token))
		r.raise_for_status()
		data_dict = r.json()['data']

		return self._build_transactions(data_dict['transactions'])

	def insert_child(self, t: ShareTransactionParent):

		data = {'transaction': {
			"account_id": self.user.account.account_id,
			"date": t.transaction_date.strftime("%Y-%m-%d"),
			"amount": - int(t.amount * 1000),
			"payee_name": t.payee_name,
			"memo": t.memo,
			"cleared": 'cleared',
			"approved": False,
			"import_id": f's||{t.share_id}'
		}}
		r = requests.post(f'{YNAB_BASE_URL}budgets/{self.user.account.budget_id}/transactions', json=data,
						  headers=self._header(self.user.token))
		r.raise_for_status()

	@staticmethod
	def _build_transactions(t_dicts: List[dict]) -> List[ShareTransaction]:
		stb = ShareTransactionBuilder()
		transactions = [stb.build(t_dict=t) for t in t_dicts]
		return transactions