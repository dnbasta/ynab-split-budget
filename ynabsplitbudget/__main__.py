import argparse
import sys
import warnings
import logging
from datetime import datetime

from ynabsplitbudget import User
from ynabsplitbudget.ynabsplitbudget import YnabSplitBudget

logging.basicConfig(level=logging.INFO)


def custom_warn(message, category, filename, lineno, file=None, line=None):
	sys.stdout.write(warnings.formatwarning(message, category, filename, lineno))


if __name__ == '__main__':
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 usage='ynabsplitbudget [-u | --user] <path/user.yaml> '
										   '[-p | --partner] <path/partner.yaml> '
										   '[-s | --split] '
										   '[-i | --push] '
										   '[-b | --balances]'
										   '[-d | --delete-orphans]'
										   '[-r | --reconcile]'
										   '[--since "YYYY-mm-dd"]')
	parser.add_argument("-u", "--user", type=str, required=True,
						help="path of config YAML to use for user")
	parser.add_argument("-p", "--partner", type=str, required=True,
						help="path of config YAML to use for partner")
	parser.add_argument("-s", "--split", action="store_true",
						help="split transactions from account")
	parser.add_argument("-i", "--push", action="store_true",
						help="push split transactions to partner account")
	parser.add_argument("-b", "--balances", action="store_true",
						help="raise error if balances of the two accounts don't match")
	parser.add_argument("-d", "--delete-orphans", action="store_true",
						help="deletes orphaned transactions in partner account")
	parser.add_argument("-r", "--reconcile", action="store_true",
						help="reconciles account if balance matches with partner account")
	parser.add_argument("--since", type=str,
						help='provide optional date if library should use something else than 30 days default')

	args = parser.parse_args()

	warnings.showwarning = custom_warn
	user = User.from_yaml(args.user)
	partner = User.from_yaml(args.partner)
	ysb = YnabSplitBudget(user=user, partner=partner)

	if args.since:
		try:
			since = datetime.strptime(args.since, "%Y-%m-%d")
		except ValueError as e:
			raise ValueError(f"Incorrect date format {args.since}, should be YYYY-mm-dd") from e
	else:
		since = None

	if args.split:
		ysb.split()
	if args.push:
		ysb.push(since=since)
	if args.delete_orphans:
		ysb.delete_orphans(since=since)
	if args.balances or args.reconcile:
		ysb.raise_on_balances_off()
	if args.reconcile:
		ysb.reconcile()


