import re

from ynabtransactionadjuster import Transaction

from ynabsplitbudget.models.exception import SplitNotValid


class SplitParser:

	@staticmethod
	def parse_split(transaction: Transaction) -> int:
		amount = transaction.amount

		try:
			r = re.search(r'@(\d+\.?\d*)(%?)', transaction.memo)
		except TypeError:
			r = None

		# return half the amount if no split attribution is found
		if r is None:
			return int(amount * 0.5)

		split_number = float(r.groups()[0])

		# return amount percentage if % in memo
		if r.groups()[1] == '%':
			if split_number <= 100:
				return int(amount * split_number / 100)
			raise SplitNotValid(f"Split is above 100% for transaction {transaction}")

		# return absolute amount
		if split_number * 1000 > abs(amount):
			raise SplitNotValid(f"Split is above total amount of {amount / 1000:.2f} for transaction {transaction}")
		sign = -1 if amount < 0 else 1
		return int(sign * split_number * 1000)
