import argparse
import json
import sys
import warnings
from dataclasses import asdict

from ynabsplitbudget.ynabsplitaccount import YnabSplitBudget


def custom_warn(message, category, filename, lineno, file=None, line=None):
	sys.stdout.write(warnings.formatwarning(message, category, filename, lineno))


if __name__ == '__main__':
	# execute only if run as the entry point into the program

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 usage='ynabsplitaccount <config_path> '
										   '[-f | --fetch] [-fi | --fetch-insert]')
	parser.add_argument("-f", "--fetch", action="store_true",
						help="fetch new transactions from both budgets")
	parser.add_argument("-fi", "--fetch-insert", action="store_true",
						help="fetch new transactions from both accounts and insert complements")
	parser.add_argument("config_path", help="path of config YAML to use")
	args = parser.parse_args()

	warnings.showwarning = custom_warn
	ysa = YnabSplitBudget(path=args.config_path)

	if args.fetch_insert:
		r = ysa.fetch_new()
		ysa.insert_complement(r)
	if args.fetch:
		sys.stdout.write(json.dumps(asdict(ysa.fetch_new())))


