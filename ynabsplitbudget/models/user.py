from dataclasses import dataclass

from ynabsplitbudget.models.account import Account


@dataclass(eq=True, frozen=True)
class User:
	name: str
	token: str
	account: Account
	flag: str
