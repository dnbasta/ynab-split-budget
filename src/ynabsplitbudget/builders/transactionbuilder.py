import re
from dataclasses import dataclass
from datetime import datetime, date
from src.ynabsplitbudget.models.transaction import Transaction, TransactionPaidSplit, TransactionOwed, Category, TransactionReference, TransactionPaidSplitPart, TransactionPaidDeleted, TransactionPaidTransfer, TransactionPaidToSplit
from src.ynabsplitbudget.config import User


@dataclass
class TransactionBuilder:
	user: User

	@classmethod
	def from_config(cls, user: User):
		return cls(user=user)

	def build(self, t_dict: dict) -> Transaction:

		has_subtransactions = True if len(t_dict['subtransactions']) > 1 else False
		has_transfer_to_splitwise = self._check_has_transfer_to_splitwise(t_dict)
		has_flag = True if t_dict['flag_color'] == 'purple' else False
		is_owed = True if t_dict['account_id'] == self.user.split_account and t_dict['transfer_account_id'] is None else False
		is_deleted = True if t_dict['deleted'] else False

		if is_owed:
			return self.build_owed(t_dict)

		if is_deleted and (has_subtransactions or has_flag or has_transfer_to_splitwise):
			return self.build_paid_deleted(t_dict)

		if has_subtransactions and has_transfer_to_splitwise:
			return self.build_paid_split(t_dict)

		if has_flag:
			return self.build_paid_to_split(t_dict)

		if has_transfer_to_splitwise:
			return self.build_paid_transfer(t_dict)

		return self.build_reference(t_dict)

	def build_paid_split(self, t_dict: dict) -> TransactionPaidSplit:
		subtransaction_transfer = next(st for st in t_dict['subtransactions']
									   if st['payee_id'] == self.user.split_transfer_payee_id)
		subtransactions_owed = [st for st in t_dict['subtransactions'] if st['id'] != subtransaction_transfer['id']]

		category = Category(id=subtransaction_transfer['category_id'],
								name=self._remove_emojis(subtransaction_transfer['category_name']))

		owed = self._convert_amount(sum((st['amount'] for st in subtransactions_owed)))
		subtransaction_id_owed = next(st['id'] for st in subtransactions_owed)

		return TransactionPaidSplit(id=t_dict['id'],
									transaction_date=self._parse_date(t_dict['date']),
									paid=self._convert_amount(t_dict['amount']),
									memo=t_dict['memo'],
									payee_name=t_dict['payee_name'],
									import_id=t_dict['import_id'],
									deleted=t_dict['deleted'],
									payee_id=t_dict['payee_id'],
									category=category,
									owed=owed,
									subtransaction_id_transfer=subtransaction_transfer['id'],
									subtransaction_id_owed=subtransaction_id_owed,
									transfer_transaction_id=subtransaction_transfer['transfer_transaction_id'],
									owner=self.user)

	def build_paid_split_part(self, t_dict: dict) -> TransactionPaidSplitPart:
		return TransactionPaidSplitPart(id=t_dict['id'],
									transaction_date=self._parse_date(t_dict['date']),
									paid=self._convert_amount(t_dict['amount']),
									memo=t_dict['memo'],
									payee_name=t_dict['payee_name'],
									import_id=t_dict['import_id'],
									deleted=t_dict['deleted'],
									payee_id=t_dict['payee_id'],
									category=None,
									owner=self.user)

	def build_paid_to_split(self, t_dict) -> TransactionPaidToSplit:
		category = Category(id=t_dict['category_id'], name=self._remove_emojis(t_dict['category_name']))
		return TransactionPaidToSplit(id=t_dict['id'],
									  transaction_date=self._parse_date(t_dict['date']),
									  paid=self._convert_amount(t_dict['amount']),
									  memo=t_dict['memo'],
									  payee_name=t_dict['payee_name'],
									  import_id=t_dict['import_id'],
									  deleted=t_dict['deleted'],
									  payee_id=t_dict['payee_id'],
									  category=category,
									  owner=self.user)

	def build_paid_transfer(self, t_dict) -> TransactionPaidTransfer:
		return TransactionPaidTransfer(id=t_dict['id'],
									   transaction_date=self._parse_date(t_dict['date']),
									   paid=self._convert_amount(t_dict['amount']),
									   memo=t_dict['memo'],
									   payee_name=t_dict['payee_name'],
									   import_id=t_dict['import_id'],
									   deleted=t_dict['deleted'],
									   payee_id=t_dict['payee_id'],
									   category=None,
									   owner=self.user)

	def build_owed(self, t_dict: dict) -> TransactionOwed:
		category = Category(id=t_dict['category_id'], name=self._remove_emojis(t_dict['category_name']))
		return TransactionOwed(id=t_dict['id'],
							   transaction_date=self._parse_date(t_dict['date']),
							   owed=self._convert_amount(t_dict['amount']),
							   memo=t_dict['memo'],
							   payee_name=t_dict['payee_name'],
							   import_id=t_dict['import_id'],
							   deleted=t_dict['deleted'],
							   payee_id=t_dict['payee_id'],
							   category=category,
							   owner=self.user)

	def build_reference(self, t_dict: dict) -> TransactionReference:
		category = Category(id=t_dict['category_id'], name=self._remove_emojis(t_dict['category_name']))
		return TransactionReference(id=t_dict['id'],
							   transaction_date=self._parse_date(t_dict['date']),
							   memo=t_dict['memo'],
							   payee_name=t_dict['payee_name'],
							   import_id=t_dict['import_id'],
							   deleted=t_dict['deleted'],
							   payee_id=t_dict['payee_id'],
							   category=category,
							   amount=self._convert_amount(t_dict['amount']),
							   owner=self.user)

	def build_paid_deleted(self, t_dict) -> TransactionPaidDeleted:
		category = Category(id=t_dict['category_id'], name=self._remove_emojis(t_dict['category_name']))
		return TransactionPaidDeleted(id=t_dict['id'],
							   transaction_date=self._parse_date(t_dict['date']),
							   paid=self._convert_amount(t_dict['amount']),
							   memo=t_dict['memo'],
							   payee_name=t_dict['payee_name'],
							   import_id=t_dict['import_id'],
							   deleted=t_dict['deleted'],
							   payee_id=t_dict['payee_id'],
							   category=category,
							   owner=self.user)

	@staticmethod
	def _remove_emojis(text: str) -> str:
		emoji = re.compile("["
						  u"\U0001F600-\U0001F64F"  # emoticons
						  u"\U0001F300-\U0001F5FF"  # symbols & pictographs
						  u"\U0001F680-\U0001F6FF"  # transport & map symbols
						  u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
						  u"\U00002500-\U00002BEF"  # chinese char
						  u"\U00002702-\U000027B0"
						  u"\U00002702-\U000027B0"
						  u"\U000024C2-\U0001F251"
						  u"\U0001f926-\U0001f937"
						  u"\U00010000-\U0010ffff"
						  u"\u2640-\u2642"
						  u"\u2600-\u2B55"
						  u"\u200d"
						  u"\u23cf"
						  u"\u23e9"
						  u"\u231a"
						  u"\ufe0f"  # dingbats
						  u"\u3030"
						  "]+", re.UNICODE)
		return re.sub(emoji, '', text).lstrip().rstrip()

	@staticmethod
	def _convert_amount(amount: int) -> float:
		return - round(float(amount) / 1000, 2)

	@staticmethod
	def _parse_date(date_str: str) -> date:
		return datetime.strptime(date_str, '%Y-%m-%d').date()

	def _check_has_transfer_to_splitwise(self, t_dict: dict) -> bool:
		if len(t_dict['subtransactions']) > 1:
			if self.user.split_account in (s['transfer_account_id'] for s in t_dict['subtransactions']):
				return True
			return False
		elif t_dict['transfer_account_id'] == self.user.split_account:
			return True
		return False

