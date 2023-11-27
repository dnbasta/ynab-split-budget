import argparse
import json
import sys
import warnings
from dataclasses import asdict

from ynabsplitaccount.ynabsplitaccount import YnabSplitAccount


def custom_warn(message, category, filename, lineno, file=None, line=None):
	sys.stdout.write(warnings.formatwarning(message, category, filename, lineno))


if __name__ == '__main__':
	# execute only if run as the entry point into the program

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 usage='ynabsplitaccount <config_path> '
										   '[-fo | --fetch-only] [-s | --sync]')
	parser.add_argument("-f", "--fetch", action="store_true",
						help="fetch contributed transactions across both budgets")
	parser.add_argument("-s", "--sync", action="store_true",
						help="sync contributed transactions across both budgets")
	parser.add_argument("config_path", help="path of config YAML to use")
	args = parser.parse_args()

	warnings.showwarning = custom_warn
	ysa = YnabSplitAccount(path=args.config_path)

	if args.sync:
		r = ysa.fetch_share_transactions()
		ysa.insert_share_transactions(r)
	if args.fetch:
		sys.stdout.write(json.dumps(asdict(ysa.fetch_share_transactions())))


