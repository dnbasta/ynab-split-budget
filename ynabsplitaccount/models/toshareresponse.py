from dataclasses import dataclass
from typing import List

from ynabsplitaccount.models.sharetransaction import ShareTransactionParent


@dataclass
class ToShareResponseItem:
	name: str
	transactions: List[ShareTransactionParent]


@dataclass
class ToShareResponse:
	user_1: ToShareResponseItem
	user_2: ToShareResponseItem
