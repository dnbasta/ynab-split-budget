from dataclasses import dataclass

from ynabsplitbudget.models.user import User


@dataclass(eq=True, frozen=True)
class Config:
	user_1: User
	user_2: User
