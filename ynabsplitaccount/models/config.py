from dataclasses import dataclass
from typing import List

import yaml

from ynabsplitaccount.models.user import User


@dataclass(eq=True, frozen=True)
class BaseConfig:
	user_1: User
	user_2: User

	def save(self):
		config_dict = {
			'user_1': {
				'name': self.user_1.name,
				'token': self.user_1.token,
				'budget': self.user_1.account.budget_name,
				'account': self.user_1.account.account_name,
				'server_knowledge': self.user_1.account.server_knowledge
			},
			'user_2': {
				'name': self.user_2.name,
				'token': self.user_2.token,
				'budget': self.user_2.account.budget_name,
				'account': self.user_2.account.account_name,
				'server_knowledge': self.user_2.account.server_knowledge
			}
		}
		with open(self.path, 'w') as f:
			yaml.safe_dump(config_dict, f)

	@property
	def users(self) -> List[User]:
		return [self.user_1, self.user_2]


@dataclass(eq=True, frozen=True)
class ConfigMissingKnowledge(BaseConfig):
	pass


@dataclass(eq=True, frozen=True)
class Config(BaseConfig):
	pass
