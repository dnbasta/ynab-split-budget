import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime
from typing import List

import requests
from requests import Response

from src.ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from src.ynabsplitbudget.builders.transactionbuilder import TransactionBuilder
from src.ynabsplitbudget.models.account import BaseAccount, Account
from src.ynabsplitbudget.models.operations import OperationInsert, OperationUpdate, OperationDelete, Operation, OperationSplit
from src.ynabsplitbudget.models.transaction import Transaction
from src.ynabsplitbudget.models.user import User

YNAB_BASE_URL = 'https://api.youneedabudget.com/v1/'


@dataclass
class BaseClient:
	token: str

	def fetch_account(self, budget_name: str, account_name: str, user_name: str) -> BaseAccount:
		r = requests.get(f'{YNAB_BASE_URL}budgets?include_accounts=true', headers=self._header())
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

	def _header(self):
		return {'Authorization': f'Bearer {self.token}'}


@dataclass
class KnowledgeClient(BaseClient):
	account: BaseAccount

	def fetch_server_knowledge(self) -> int:
		r = requests.get(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/accounts', headers=self._header())
		self._check_response(r)
		r_dict = r.json()
		server_knowledge = r_dict['data']['server_knowledge']
		return server_knowledge


@dataclass
class TransactionClient(KnowledgeClient):
	account: Account
	transaction_builder: TransactionBuilder

	@classmethod
	def from_config(cls, user: User):
		return cls(token=user.token,
				   account=user.account,
				   transaction_builder=TransactionBuilder.from_config(user=user))

	def fetch_changed(self) -> (List[Transaction], int):
		params = {'last_knowledge_of_server': self.account.server_knowledge}
		r = requests.get(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/transactions',
						 params=params,
						 headers=self._header())
		self._check_response(r)
		r_dict = r.json()

		transactions_dicts = self._filter_transactions_to_ignore(r_dict['data']['transactions'])
		transactions = [self.transaction_builder.build(t_dict=t) for t in transactions_dicts]
		server_knowledge = r_dict['data']['server_knowledge']
		return transactions, server_knowledge

	def fetch_lookup(self, since: date):
		params = {'since_date': datetime.strftime(since, '%Y-%m-%d')}
		r = requests.get(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/transactions',
						 params=params,
						 headers=self._header())
		self._check_response(r)
		r_dict = r.json()

		transactions = [self.transaction_builder.build(t_dict=t) for t in r_dict['data']['transactions']]
		return transactions

	def process_operation(self, operation: Operation):
		if isinstance(operation, OperationInsert):
			self._insert(operation)
		elif isinstance(operation, (OperationUpdate, OperationSplit)):
			self._update(operation)
		elif isinstance(operation, OperationDelete):
			self._delete(operation)

	def _insert(self, ynab_op: OperationInsert) -> (int, int, int):
		data = {'transactions': [{**ynab_op.as_dict(), **{'account_id': self.account.account_id}}]}
		r = requests.post(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/transactions', json=data, headers=self._header())
		self._check_response(r)

		r_dict = r.json()
		duplicate_import_ids = r_dict['data']['duplicate_import_ids']
		server_knowledge = r_dict['data']['server_knowledge']
		inserted_transactions = [self.transaction_builder.build(ji) for ji in r_dict['data']['transactions']]
		return duplicate_import_ids, server_knowledge, inserted_transactions

	def _update(self, ynab_op: [OperationUpdate, OperationSplit]) -> None:
		data = {'transaction': ynab_op.as_dict()}
		r = requests.put(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/transactions/{ynab_op.id}', json=data,
						 headers=self._header())
		self._check_response(r)

	def _delete(self, ynab_op: OperationDelete) -> None:
		r = requests.delete(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/transactions/{ynab_op.id}',
							headers=self._header())
		self._check_response(r)

	def fetch_balance(self) -> float:
		r = requests.get(f'{YNAB_BASE_URL}budgets/{self.account.budget_id}/accounts/{self.account.account_id}',
						 headers=self._header())
		self._check_response(r)
		r_dict = r.json()

		amount = round(float(r_dict['data']['account']['balance']) / 1000, 2)
		return amount

	@staticmethod
	def _filter_transactions_to_ignore(transactions_dict: List[dict]) -> List[dict]:
		non_reconciled = [t for t in transactions_dict if t['cleared'] != 'reconciled']
		return non_reconciled
