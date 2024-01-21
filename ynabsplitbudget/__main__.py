import argparse
import sys
import warnings

from ynabsplitbudget.ynabsplitbudget import YnabSplitBudget


def custom_warn(message, category, filename, lineno, file=None, line=None):
	sys.stdout.write(warnings.formatwarning(message, category, filename, lineno))


if __name__ == '__main__':
	# execute only if run as the entry point into the program

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 usage='ynabsplitaccount [-c | --config-path] <config_path> '
										   '[-u | --user-name] <user_name> '
										   '[-s | --split-transactions] [-i | --insert-complements]')
	parser.add_argument("-u", "--user-name", type=str, help="user to do the action for", required=True)
	parser.add_argument("-c", "--config-path", type=str, help="path of config YAML to use")
	parser.add_argument("-s", "--split-transactions", action="store_true",
						help="split transactions from account")
	parser.add_argument("-i", "--insert-complements", action="store_true",
						help="fetch new transactions from both accounts and insert complements")
	parser.add_argument("-b", "--check-balances", action="store_true",
						help="raise error if balances of the two accounts don't match")

	args = parser.parse_args()

	warnings.showwarning = custom_warn
	ysb = YnabSplitBudget(path=args.config_path, user=args.user_name)

	if args.split_transactions:
		ysb.split_transactions()
	if args.insert_complements:
		ysb.insert_complements()
	if args.check_balances:
		ysb.raise_on_balance_mismatch()


