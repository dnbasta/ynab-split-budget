import hashlib
import re
from dataclasses import dataclass
from typing import Optional, Union

from src.ynabsplitbudget.models.transaction import TransactionPaidSplit, TransactionOwed, TransactionPaid, TransactionReference, TransactionPaidSplitPart, TransactionPaidDeleted, TransactionPaidToSplit, TransactionPaidTransfer, Transaction
from src.ynabsplitbudget.models.charge import Charge, ChargeNew, ChargeOwnerDeleted, ChargeNewIncompleteRecipient, ChargeRecipientDeleted, ChargeNewIncompleteOwner, ChargeChanged
from src.ynabsplitbudget.models.user import User
from src.ynabsplitbudget.repositories.transactionlookuprepository import TransactionLookupRepository


@dataclass
class ChargeBuilder:
	user_1_lookup: TransactionLookupRepository
	user_2_lookup: TransactionLookupRepository
	user_1: User
	user_2: User

	def from_transaction(self, t: Transaction) -> Optional[Charge]:
		if isinstance(t, TransactionPaid):
			return self.from_owner_transaction(transaction=t)
		elif isinstance(t, TransactionOwed):
			return self.from_recipient_transaction(transaction=t)
		elif isinstance(t, TransactionReference):
			return self.from_reference(transaction=t)

	def from_owner_transaction(self, transaction: TransactionPaid) -> Optional[Charge]:

		# exchange Split part with actual Split Transaction
		if isinstance(transaction, TransactionPaidSplitPart):
			transaction = self.fetch_lookup(transaction.owner).fetch_parent_by_transfer_transaction_id(transaction.id)

		other_user = self._fetch_other_user(transaction.owner)
		lookup = self.fetch_lookup(other_user)
		if recipient_transaction := lookup.fetch_recipient_by_hashed_id(encrypt(transaction.id)):

			if isinstance(transaction, TransactionPaidDeleted) and not recipient_transaction.deleted:
				return self._build_owner_deleted(owner_transaction=transaction,
												 recipient_transaction_id=recipient_transaction.id)

			if isinstance(transaction, (TransactionPaidSplit, TransactionPaidTransfer)):
				if recipient_transaction.deleted:
					return self._build_recipient_deleted(owner_transaction=transaction,
														 recipient_transaction_id=recipient_transaction.id)
				if (recipient_transaction.owed != transaction.paid - transaction.owed
						or isinstance(recipient_transaction, TransactionReference)):
					return self._build_changed(owner_transaction=transaction,
											   recipient_transaction=recipient_transaction)

			if isinstance(transaction, TransactionPaidToSplit):
				if recipient_transaction.deleted:
					return self._build_paid_new(transaction=transaction)

				return self._build_owner_incomplete(owner_transaction=transaction,
													recipient_transaction=recipient_transaction)

		else:

			if isinstance(transaction, (TransactionPaidSplit, TransactionPaidTransfer)):
				return self._build_recipient_incomplete(transaction=transaction)

			if isinstance(transaction, TransactionPaidToSplit):
				return self._build_paid_new(transaction=transaction)

	def from_recipient_transaction(self, transaction: TransactionOwed) -> Optional[Charge]:

		# try fetching connected transaction
		if transaction.import_id is not None:
			charge_id = self._fetch_charge_id_from_owed(transaction)
			lookup = self.fetch_lookup(self._fetch_other_user(transaction.owner))
			owner_transaction = lookup.fetch_owner_by_hashed_id(charge_id)

			if isinstance(owner_transaction, (TransactionPaidSplit, TransactionPaidTransfer)):
				if transaction.deleted:
					return self._build_recipient_deleted(owner_transaction=owner_transaction,
														recipient_transaction_id=transaction.id)
				elif transaction.owed != owner_transaction.paid - owner_transaction.owed:
					return self._build_changed(owner_transaction=owner_transaction,
											   recipient_transaction=transaction)

			if isinstance(owner_transaction, TransactionReference) and not transaction.deleted:
				return self._build_owner_deleted(owner_transaction=owner_transaction,
												 recipient_transaction_id=transaction.id)

	def from_reference(self, transaction: TransactionReference) -> Optional[Charge]:
		lookup = self.fetch_lookup(self._fetch_other_user(transaction.owner))
		if owner_transaction := lookup.fetch_owner_by_hashed_id(self._fetch_charge_id_from_owed(transaction)):
			if isinstance(owner_transaction, TransactionPaid):
				return self.from_owner_transaction(transaction=owner_transaction)

		if recipient_transaction := lookup.fetch_recipient_by_hashed_id(encrypt(transaction.id)):
			if isinstance(recipient_transaction, TransactionOwed):
				return self.from_recipient_transaction(transaction=recipient_transaction)

	def _build_paid_new(self, transaction: [TransactionPaidToSplit, TransactionPaidTransfer]) -> ChargeNew:
		hashed_id = encrypt(transaction.id)
		memo = self._create_memo_paid(memo=transaction.memo,
									  paid=transaction.paid,
									  payee_name=transaction.payee_name,
									  user=transaction.owner)
		if isinstance(transaction, TransactionPaidTransfer):
			owner_owed = 0
			recipient_owed = transaction.paid
		else:
			owner_owed, recipient_owed = self._calculate_owed(memo=transaction.memo, paid=transaction.paid)

		return ChargeNew(id=hashed_id,
						 owner_transaction_id=transaction.id,
						 paid=transaction.paid,
						 owner_owed=owner_owed,
						 recipient_owed=recipient_owed,
						 payee_name=transaction.payee_name,
						 charge_date=transaction.transaction_date,
						 memo=memo,
						 owner=transaction.owner,
						 owner_category=transaction.category,
						 recipient=self._fetch_other_user(transaction.owner))

	def _build_owner_deleted(self, owner_transaction: [TransactionPaid, TransactionReference],
							 recipient_transaction_id: Optional[str]) -> ChargeOwnerDeleted:
		return ChargeOwnerDeleted(id=encrypt(owner_transaction.id),
								  paid=owner_transaction.paid,
								  owner_owed=None,
								  recipient_owed=None,
								  payee_name=owner_transaction.payee_name,
								  memo=owner_transaction.memo,
								  charge_date=owner_transaction.transaction_date,
								  owner_category=owner_transaction.category,
								  recipient_transaction_id=recipient_transaction_id,
								  owner_transaction_id=owner_transaction.id,
								  owner=owner_transaction.owner,
								  recipient=self._fetch_other_user(owner_transaction.owner))

	def _build_owner_deleted_from_recipient(self, recipient_transaction: TransactionOwed) -> ChargeOwnerDeleted:
		return ChargeOwnerDeleted(id=self._fetch_charge_id_from_owed(recipient_transaction),
								  paid=None,
								  owner_owed=None,
								  recipient_owed=recipient_transaction.owed,
								  payee_name=recipient_transaction.payee_name,
								  memo=recipient_transaction.memo,
								  charge_date=recipient_transaction.transaction_date,
								  owner_category=recipient_transaction.category,
								  recipient_transaction_id=recipient_transaction.id,
								  owner_transaction_id=None,
								  owner=self._fetch_other_user(recipient_transaction.owner),
								  recipient=recipient_transaction.owner)

	def _build_recipient_deleted(self, owner_transaction: [TransactionPaidSplit, TransactionPaidTransfer],
							 recipient_transaction_id: Optional[str]) -> ChargeRecipientDeleted:
		return ChargeRecipientDeleted(id=encrypt(owner_transaction.id),
									  paid=owner_transaction.paid,
									  owner_owed=owner_transaction.owed,
									  recipient_owed=owner_transaction.paid - owner_transaction.owed,
									  payee_name=owner_transaction.payee_name,
									  memo=owner_transaction.memo,
									  charge_date=owner_transaction.transaction_date,
									  owner_category=owner_transaction.category,
									  recipient_transaction_id=recipient_transaction_id,
									  owner_transaction_id=owner_transaction.id,
									  owner=owner_transaction.owner,
									  recipient=self._fetch_other_user(owner_transaction.owner))

	def _build_changed(self, owner_transaction: [TransactionPaidSplit, TransactionPaidTransfer],
					   recipient_transaction: Optional[Union[TransactionOwed, TransactionReference]]) -> Optional[ChargeChanged]:
		hashed_id = encrypt(owner_transaction.id)
		memo = self._create_memo_paid(memo=owner_transaction.memo,
									  paid=owner_transaction.paid,
									  payee_name=owner_transaction.payee_name,
									  user=owner_transaction.owner)
		return ChargeChanged(id=hashed_id,
							 owner_transaction_id=owner_transaction.id,
							 recipient_transaction_id=recipient_transaction.id,
							 paid=owner_transaction.paid,
							 owner_owed=owner_transaction.owed,
							 recipient_owed=owner_transaction.paid - owner_transaction.owed,
							 payee_name=owner_transaction.payee_name,
							 charge_date=owner_transaction.transaction_date,
							 owner_category=owner_transaction.category,
							 memo=memo,
							 owner=owner_transaction.owner,
							 recipient=self._fetch_other_user(owner_transaction.owner))

	def _build_recipient_incomplete(self, transaction: [TransactionPaidSplit, TransactionPaidTransfer]) -> ChargeNewIncompleteRecipient:
		memo = self._create_memo_paid(memo=transaction.memo,
									  paid=transaction.paid,
									  payee_name=transaction.payee_name,
									  user=transaction.owner)
		return ChargeNewIncompleteRecipient(id=encrypt(transaction.id),
											owner_transaction_id=transaction.id,
											paid=transaction.paid,
											owner_owed=transaction.owed,
											recipient_owed=transaction.paid - transaction.owed,
											payee_name=transaction.payee_name,
											charge_date=transaction.transaction_date,
											owner_category=transaction.category,
											memo=memo,
											owner=transaction.owner,
											recipient=self._fetch_other_user(transaction.owner))

	def _build_owner_incomplete(self, owner_transaction: TransactionPaidToSplit,
								recipient_transaction: TransactionOwed) -> ChargeNewIncompleteOwner:
		memo = self._create_memo_paid(memo=owner_transaction.memo,
									  paid=owner_transaction.paid,
									  payee_name=owner_transaction.payee_name,
									  user=owner_transaction.owner)
		owner_owed, recipient_owed = self._calculate_owed(paid=owner_transaction.paid, memo=owner_transaction.memo)
		return ChargeNewIncompleteOwner(id=encrypt(owner_transaction.id),
										owner_transaction_id=owner_transaction.id,
										paid=owner_transaction.paid,
										owner_owed=owner_owed,
										recipient_owed=recipient_owed,
										payee_name=owner_transaction.payee_name,
										charge_date=owner_transaction.transaction_date,
										owner_category=owner_transaction.category,
										memo=memo,
										owner=owner_transaction.owner,
										recipient=recipient_transaction.owner,
										recipient_transaction_id=recipient_transaction.id)

	def _calculate_owed(self, paid: float, memo: str) -> (float, float):
		if split_pct := self._parse_split_pct(share_str=memo):
			owner_owed = round(paid * split_pct, 2)
		else:
			owner_owed = round(paid / 2, 2)
		return owner_owed, paid - owner_owed

	def _create_memo_paid(self, memo: str, paid: float, payee_name: str, user: User) -> str:
		if memo in (None, ''):
			memo = payee_name
		else:
			memo = self._parse_genuine_memo(memo)

		if float(paid) < 0:
			memo += f' (Refund from {user.name})'

		return memo

	@staticmethod
	def _parse_genuine_memo(memo_str: str) -> Optional[str]:
		if memo_str is not None:
			share_str = re.search(r"(@[0-9]*)", str(memo_str))
			if share_str is not None:
				memo_str = memo_str.replace(share_str[1], '')
			return memo_str

	@staticmethod
	def _parse_split_pct(share_str: str) -> Optional[float]:
		re_result = re.search(r'@([0-9]?[0-9]?)', str(share_str))
		if re_result and re_result.group(1).isdigit():
			return float(re_result.group(1)) / 100

	@staticmethod
	def _fetch_charge_id_from_owed(t: [TransactionOwed, TransactionReference]) -> str:
		if t.import_id and '||' in t.import_id:
			return t.import_id.split('||')[1][:-2]

	@staticmethod
	def _create_charge_id(t: [TransactionPaid, TransactionReference]) -> str:
		return encrypt(t.id)

	def _fetch_other_user(self, user: User) -> User:
		if user == self.user_1:
			return self.user_2
		return self.user_1

	def fetch_lookup(self, user: User) -> TransactionLookupRepository:
		if user == self.user_1:
			return self.user_1_lookup
		return self.user_2_lookup


def encrypt(val: Optional[Union[str, int]]) -> str:
	return hashlib.shake_128(str(val).encode()).hexdigest(10)
