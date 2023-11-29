# ynab-split-budget

[![GitHub Release](https://img.shields.io/github/release/dnbasta/ynab-split-budget?style=flat)]() 

This library enables cost sharing across two YNAB budgets. It requires two dedicated accounts in each budget to which
each budget owner can transfer amounts from their own budget. Each transfer is considered as its opposite in the other 
account.

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
  name: <user_name>
  token: <ynab_token>
  budget: <ynab_budget_name>
  account: <ynab_budget_account_name>
  flags:
    - color: blue
      split: 0.5
    - color: purple
      split: 0.33
user_2:
  name: <user_name>
  token: <ynab_token>
  budget: <ynab_budget_name>
  account: <ynab_budget_account_name>
  flags:
    - color: orange
      split: 0.5
    - color: red
      split: 0.25
```

## Usage
1. Create a transaction somewhere in your budget and add one of the defined color flags. It needs to be cleared and not
yet reconciled to be picked up by the library.
2. Run the split functionality either as python library or from the command line.
```py
from ynabsplitbudget import YnabSplitBudget

ynab_split_budget = YnabSplitBudget('path/config.yaml')
ynab_split_budget.split_transactions('user_name')

```
```bash
$ python -m -c <path/config.yaml> -u <user_name> -s | --sync-transactions
```
3. Clear the newly split transactions in the account you created for sharing.
4. Run the insert functionality either as python library or from the command line
```py
ynab_split_budget.insert_complements('user_name')

```
```bash
$ python -m -c <path/config.yaml> -u <user_name> -i | --insert-complements
```
## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
