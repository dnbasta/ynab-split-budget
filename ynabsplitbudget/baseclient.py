import requests

from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


class BaseClient:

	def __init__(self, token: str, user_name: str):
		self.session = requests.Session()
		self.session.headers = {'Authorization': f'Bearer {token}'}
		self.user_name = user_name

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
