from src.ynabsplitbudget.models.account import Account
from src.ynabsplitbudget.models.config import ConfigMissingKnowledge


class NoServerKnowledge(Exception):

	def __init__(self, config: ConfigMissingKnowledge):
		msu = ' '.join([f'Account for {u.name} has no server knowledge.'
						for u in config.users if not isinstance(u.account, Account)])
		warning_msg = f'{msu} Please run python -m ynabsplitbudget [CONFIG.YAML] -s to fetch current knowledge from server'
		super().__init__(warning_msg)


class BudgetNotFound(Exception):
	pass


class AccountNotFound(Exception):
	pass
