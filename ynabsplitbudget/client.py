from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Union, Tuple
from unicodedata import category

import requests
from requests import HTTPError

from ynabsplitbudget.models.transaction import InsertTransaction
from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.exception import BudgetNotFound, AccountNotFound
from ynabsplitbudget.transactionbuilder import TransactionBuilder
from ynabsplitbudget.models.transaction import RootTransaction, LookupTransaction, ComplementTransaction

YNAB_BASE_URL = 'https://api.ynab.com/v1/'


@dataclass
class Client:

    def __init__(self, user_name: str, budget_id: str, account_id: str, token: str):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {token}'})
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

    def insert_complements(self, transactions: List[RootTransaction]) -> List[ComplementTransaction]:
        insert_transactions = [InsertTransaction(id=t.id,
                                                 amount=t.amount,
                                                 share_id=t.share_id,
                                                 memo=t.memo,
                                                 transaction_date=t.transaction_date,
                                                 payee_name=t.payee_name,
                                                 account_id=t.account_id,
                                                 iteration=0) for t in transactions]
        complements, duplicates = self._insert(insert_transactions)
        while duplicates:
            complements_d, duplicates = self._insert_duplicates(insert_transactions, duplicates)
            complements += complements_d
        return complements

    def _insert(self, transactions: List[InsertTransaction]) -> Tuple[List[ComplementTransaction], List[str]]:
        url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/transactions'
        data = [{
            "account_id": self.account_id,
            "date": t.transaction_date.strftime("%Y-%m-%d"),
            "amount": - t.amount,
            "payee_name": t.payee_name,
            "memo": t.memo,
            "cleared": 'cleared',
            "approved": False,
            "import_id": f's||{t.share_id}||{t.iteration}'
        } for t in transactions]
        if data:
            r = self.session.post(url, json=dict(transactions=data))
            r.raise_for_status()
            return ([self.transaction_builder.build_complement(c) for c in r.json()['data']['transactions']],
                    r.json()['data']['duplicate_import_ids'])
        return [], []

    def _insert_duplicates(self, transactions: List[InsertTransaction],
                           duplicate_ids: List[str]) -> Tuple[List[ComplementTransaction], List[str]]:
        iteration_lookup = {did.split('||')[1]: int(did.split('||')[2])
                            for did in duplicate_ids
                            if 's||' in did and len(did.split('||')) == 3}
        duplicate_transactions = [t for t in transactions if t.share_id in iteration_lookup.keys()]
        for t in duplicate_transactions:
            t.iteration = iteration_lookup[t.share_id] + 1
        complements, duplicates = self._insert(duplicate_transactions)
        return complements, duplicates

    def fetch_balance(self) -> int:
        url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/accounts/{self.account_id}'
        r = self.session.get(url)
        r.raise_for_status()
        balance = r.json()['data']['account']['balance']
        return balance

    def delete_complement(self, transaction_id: str) -> None:
        url = f'{YNAB_BASE_URL}budgets/{self.budget_id}/transactions/{transaction_id}'
        r = self.session.delete(url)
        r.raise_for_status()
