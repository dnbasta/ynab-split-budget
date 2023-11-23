# ynab-split-budget

[![GitHub Release](https://img.shields.io/github/release/dnbasta/ynab-split-budget?style=flat)]() 

This library enables cost sharing across two YNAB budgets. It requires two dedicated accounts in each budget to which
each budget owner can transfer amounts from their own budget. This transfer is considered as an asset and 
creates a liability of equal size in the other account.

## Preparations in YNAB
1. Create a checking account for the cost sharing in both YNAB budgets.
2. Create a personal access token for both budgets as described [here](https://api.ynab.com/)

## Install library from PyPI

```bash
pip install ynab-split-budget
```

## Create `config.yaml`
Save the file at a convenient space and provide the path and name to the library when initializing
```yaml
user_1:
  name: <name>
  token: <ynab_token>
  budget: <ynab_budget_name>
  account: <ynab_budget_account>
user_2:
  name: <name>
  token: <ynab_token>
  budget: <ynab_budget_name>
  account: <ynab_budget_account>
```
## Fetch current Server Knowledge
 The server knowledge represents the current knowledge state of a YNAB account. It is an integer which increases 
 each time there is a change in the respective account. This library uses the server knowledge to determine which
 changes have not been considered yet. It updates the server knowledge after each process run and writes the values 
 into the config file.

#### via command line
```bash
$ python -m <path/config.yaml> -s
server knowledge: <user_1_name>: <int>, <user_2_name>: <int>
```
#### as python library
```python
from ynabsplitbudget import YnabSplitBudget

ynab_split_budget = YnabSplitBudget()
ynab_split_budget.load_config(path='path/config.yaml')
ynab_split_budget.update_server_knowledge()
```
## Usage

### YNAB
#### Option 1: 
Create a transfer to the cost sharing account.
#### Option 2:
Mark a transaction in your budget with the purple flag. This library will detect that transaction and create a 
by default a 50% split transaction and transfer that to the cost sharing account. If you would like an automatic split 
with another percentage you can put a marker in the form of `@<int>` the memo line. This will create a transfer 
transaction with that percentage amount.


### ynab-split-budget

#### as python library

```py
from ynabsplitbudget import YnabSplitBudget

# initialize
ynab_split_budget = YnabSplitBudget()
ynab_split_budget.load_config(path='path/config.yaml')

# fetch charges which require sync
fetch_response = ynab_split_budget.fetch_charges()

# sync charges across both accounts
ynab_split_budget.process_charges(fetch_response)
```
#### via command line
```bash
# fetch and process charges which require sync
$ python -m <path/config.yaml> -p
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.