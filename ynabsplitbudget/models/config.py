from dataclasses import dataclass

from ynabsplitbudget.models.user import User


@dataclass
class Config:
	"""Configuration object to use for YnabSplitBudget instance

	:ivar user: User which to use for the instance
	:ivar partner: Partner which to use for the instance
	"""
	user: User
	partner: User

	@classmethod
	def from_dict(cls, data: dict) -> 'Config':
		"""Creates a Config object from a dict."""
		return cls(user=User.from_dict(data['user']), partner=User.from_dict(data['partner']))
