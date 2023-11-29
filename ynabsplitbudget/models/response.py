from dataclasses import dataclass
from typing import List

from ynabsplitbudget.models.transaction import RootTransaction


@dataclass
class ResponseItem:
	name: str
	transactions: List[RootTransaction]


@dataclass
class Response:
	user_1: ResponseItem
	user_2: ResponseItem
