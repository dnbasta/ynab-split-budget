from src.ynabsplitbudget.ynabsplitbudget import YnabSplitBudget


def test_from_config(prod_conf):
	ysb = YnabSplitBudget()
	ysb.load_config(prod_conf)
