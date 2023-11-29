from dataclasses import dataclass
from typing import List

from ynabsplitbudget.models.account import Account
from ynabsplitbudget.models.categorysplit import CategorySplit
from ynabsplitbudget.models.flagsplit import FlagSplit


@dataclass(eq=True, frozen=True)
class User:
	name: str
	token: str
	account: Account
	flag_splits: List[FlagSplit]
	category_splits: List[CategorySplit]
