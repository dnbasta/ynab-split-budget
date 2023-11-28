from dataclasses import dataclass
from typing import Union

from ynabsplitaccount.models.account import Account


@dataclass(eq=True, frozen=True)
class User:
	name: str
	token: str
	account: Account
