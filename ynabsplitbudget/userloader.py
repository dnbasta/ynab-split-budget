from ynabsplitbudget.client import BaseClient
from ynabsplitbudget.models.exception import ConfigNotValid, UserNotFound
from ynabsplitbudget.models.user import User


class UserLoader:

	def __init__(self, config_dict: dict):
		self._config_dict = config_dict

		if len(self._config_dict) != 2:
			raise ConfigNotValid('Config needs to have exactly 2 user entries')

		for u, entries in self._config_dict.items():
			for e in ['account', 'budget', 'token', 'flag']:
				if e not in entries.keys():
					raise ConfigNotValid(f"'{e}' missing for user '{u}'")

	def load(self, user) -> User:

		try:
			user_dict = self._config_dict[user]
			c = BaseClient(token=user_dict['token'], user_name=user)
			account = c.fetch_account(budget_id=user_dict['budget'], account_id=user_dict['account'])
			return User(name=user, token=user_dict['token'], account=account, flag=user_dict['flag'])

		except KeyError:
			raise UserNotFound(f"{user} not found in config")

	def load_partner(self, user: str) -> User:
		partner = next(k for k in self._config_dict.keys() if k != user)
		return self.load(user=partner)
