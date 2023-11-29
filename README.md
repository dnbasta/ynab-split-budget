# ynab-split-account

[![GitHub Release](https://img.shields.io/github/release/dnbasta/ynab-split-budget?style=flat)]() 

This library enables cost sharing across two YNAB budgets. It requires two dedicated accounts in each budget to which
each budget owner can transfer amounts from their own budget. Each transfer is considered as its opposite in the other 
account.

## Preparations in YNAB
1. Create a checking account for the cost sharing in both YNAB budgets.
2. Create a personal access token for both budgets as described [here](https://api.ynab.com/)

## Install library from PyPI

```bash
pip install ynab-split-account
```

## Create `config.yaml`
Save the file at a convenient space and provide the path and name to the library when initializing
```yaml
user_1:
  name: <name>
  token: <ynab_token>
  budget: <ynab_budget_name>
  account: <ynab_budget_account_name>
user_2:
  name: <name>
  token: <ynab_token>
  budget: <ynab_budget_name>
  account: <ynab_budget_account_name>
```

## Usage
1. Create a transaction in or transfer to the cost sharing account in YNAB. It needs to be cleared and not yet 
reconciled in order to be recognized by the library.
2. Run this library either as python libary or from the command line 
#### as python library

```py
from ynabsplitbudget import YnabSplitAccount

# initialize
ynab_split_account = YnabSplitAccount(path='path/config.yaml')

# fetch new transactions from both accounts
transactions_to_share = ynab_split_account.fetch_new()

# insert complement transactions in partner account
ynab_split_account.insert_complement(transactions_to_share)
```
#### via command line
```bash
# fetch new transactions from both accounts and insert complements
$ python -m <path/config.yaml> -fi | --fetch-insert
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
