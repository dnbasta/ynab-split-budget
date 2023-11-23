from dataclasses import dataclass
from typing import Union

from src.ynabsplitbudget.models.account import Account, BaseAccount


@dataclass(eq=True, frozen=True)
class User:
	name: str
	token: str
	account: Union[Account, BaseAccount]
