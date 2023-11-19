# project_name

[![GitHub Release](https://img.shields.io/github/release/dnbasta/ynab-split-budget?style=flat)]() 

project_description

## Install it from PyPI

```bash
pip install ynab-split-budget
```

## Create `config.yaml`

## Usage

```py
from ynabsplitbudget import YnabSplitBudget

# initialize
ynab_split_budget = YnabSplitBudget.from_config()

# fetch charges which require sync
fetch_response = ynab_split_budget.fetch_charges()

# process charges
ynab_split_budget.process_charges(fetch_response)
```

```bash
$ python -m project_name
#or
$ project_name
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.