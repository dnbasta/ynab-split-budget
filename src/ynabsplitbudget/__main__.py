import argparse
import json
import sys
import warnings
from dataclasses import asdict

from src.ynabsplitbudget.ynabsplitbudget import YnabSplitBudget


def custom_warn(message, category, filename, lineno, file=None, line=None):
	sys.stdout.write(warnings.formatwarning(message, category, filename, lineno))


if __name__ == '__main__':
	# execute only if run as the entry point into the program

	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 usage='ynabsplitbudget <config_path> [-s | --sync-server-knowledge] '
										   '[-fo | --fetch-only] [-fp | --fetch-process]')
	parser.add_argument("-s", "--sync-knowledge", action="store_true",
						help="update server knowledge to current value")
	parser.add_argument("-f", "--fetch", action="store_true",
						help="fetch charges across both budgets")
	parser.add_argument("-p", "--process", action="store_true",
						help="fetch and process charges across both budgets")
	parser.add_argument("config_path", help="path of config YAML to use")
	args = parser.parse_args()

	warnings.showwarning = custom_warn
	ysb = YnabSplitBudget()
	ysb.load_config(path=args.config_path)

	if args.process:
		r = ysb.fetch_charges()
		ysb.process_charges(r)
	if args.fetch:
		sys.stdout.write(json.dumps(asdict(ysb.fetch_charges())))
	elif args.sync_knowledge:
		ysb.update_server_knowledge()

