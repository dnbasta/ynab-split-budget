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
Create a file with below content. 

You can find the ID of the budget and of the account if you go to https://app.ynab.com/ and open the target account by
clicking on the name on the left hand side menu. The URL does now contain both IDs 
`https://app.ynab.com/<budget_id>/accounts/<account_id>`

Save the file at a convenient place and provide the path to the library when initializing
```yaml
user_name:
  token: <ynab_token>
  budget: <budget_id>
  account: <account_id>
  flag: purple
partner_name:
  token: <ynab_token>
  budget: <budget_id>
  account: <account_id>
  flag: blue
```

## Usage
### 1. Create a transaction
Create a transaction in your budget and add the defined color flag. Only cleared transactions will be considered. 
By default, the transaction will be split in half, but you can specify a different split by adding
`@x%` for percentage or `@x` for specific amount in the memo of the transaction. The amount you specify
in this split will be transferred to your sharing account. You can also create a plain transfer to the shared account 
which will be completely allocated to the partner account.
### 2. Run the split functionality
```py
from ynabsplitbudget import YnabSplitBudget

ynab_split_budget = YnabSplitBudget(path='path/config.yaml', user='<user_name>')
ynab_split_budget.split_transactions()
```
### 3. Clear the newly split transaction
Using the YNAB web interface go to your split account and clear the newly split transaction over there. 
This can currently not be automated as YNAB API can't clear split transactions at this point in time.
### 4. Run the insert functionality
```py
ynab_split_budget.insert_complements()
```
### 5. (Optional) Check Balances
Additionally you can check if the cleared balances in both accounts match. If they don't match you will get back a
`BalancesDontMatch` Error which also gives you the two values of the balances.
```py
ynab_split_budget.raise_on_balances_off()
```
## Run via bash commands
You can run this package also from bash with the following commands
```bash
$ python -m ynabsplitbudget -c <path/config.yaml#user_name> -s | --split-transactions
$ python -m ynabsplitbudget -c <path/config.yaml#user_name> -i | --insert-complements
$ python -m ynabsplitbudget -c <path/config.yaml#user_name> -b | --check-balances
```
## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
