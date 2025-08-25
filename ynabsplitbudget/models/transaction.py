from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class RootTransaction:
    id: str
    share_id: str
    transaction_date: date
    memo: str
    payee_name: str
    amount: float
    account_id: str


@dataclass
class ComplementTransaction:
    id: str
    share_id: str
    transaction_date: date
    memo: str
    payee_name: str
    amount: float
    account_id: str
    iteration: int


@dataclass
class LookupTransaction:
    account_id: str
    payee_name: str
    transfer_transaction_ids: List[str]

@dataclass
class InsertTransaction:
    id: str
    share_id: str
    transaction_date: date
    memo: str
    payee_name: str
    amount: float
    account_id: str
    iteration: int
