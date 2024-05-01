# ynab-split-budget

[![GitHub Release](https://img.shields.io/github/release/dnbasta/ynab-split-budget?style=flat)]() 
[![Github Release](https://img.shields.io/maintenance/yes/2100)]()
[![Monthly downloads](https://img.shields.io/pypi/dm/ynab-split-budget)]()

This library enables cost sharing across two YNAB budgets. It requires two dedicated accounts in each budget to which
each budget owner can transfer amounts from their own budget. Each transfer is considered as its opposite in the other 
account.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/dnbasta)

## Preparations in YNAB
1. Create a checking account for the cost sharing in both YNAB budgets.
2. Create a personal access token for both budgets as described [here](https://api.ynab.com/)

## Install library from PyPI

```bash
pip install ynab-split-budget
```
## Usage
### 1. Create a transaction
Create a transaction in the budget and add a specific flag in a specific color to be used for the splits. The 
transaction needs to be cleared in order to be considered by this library. By default, the transaction will be split 
in half, but you can specify a different split by adding `@x%` for percentage or `@x` for specific amount in the memo 
of the transaction. The amount you specify in this split will be transferred to your sharing account. You can also 
create a plain transfer to the shared account which will be completely allocated to the partner account.

### 2. Initialize library
You can find the ID of the budget and of the account if you go to https://app.ynab.com/ and open the target account by
clicking on the name on the left hand side menu. The URL does now contain both IDs 
`https://app.ynab.com/<budget_id>/accounts/<account_id>`
Possible colors for the flag value are `red`, `orange`, `yellow`, `green`, `blue` and `purple`
```py
from ynabsplitbudget import YnabSplitBudget, User

user = User(name='<name>', token='<token>', budget_id='<budget_id>', account_id='<account_id', 
            flag_color='<flag_color>')
partner = User(name='<name>', token='<token>', budget_id='<budget_id>', account_id='<account_id', 
            flag_color='<flag_color>')

ynab_split_budget = YnabSplitBudget(partner=partner)
```
### 3. Split transactions
Call the `split()` method of the instance. It will split flagged transactions in the budget into a subtransaction with
the original category and a transfer to the split account. By default, the transfer transactions will show up as 
uncleared in the split account. The optional `clear` parameter allows to automatically clear the transactions in 
the split account. The function returns the updated transactions after applying the split.
```py
ynab_split_budget.split()
```

### 4. Push new splits to partner split account
Calling the `push()` function will insert new transactions from user split account into split account of partner to keep
both accounts in sync. By default, the function will compare and insert transactions of the last 30 days. Optionally it 
takes a `since` parameter in the form of `datetime.date` to set a timeframe different from 30 days. 

```py
ynab_split_budget.push()
```
## Advanced Usage
### Check Balances
The `raise_on_balances_off()` function compares the cleared balances in both split accounts. If they don't match it 
will raise a `BalancesDontMatch` error which includes the values of the balances.
```py
ynab_split_budget.raise_on_balances_off()
```
### Delete Orphaned Complements
The `delete_orphans()` function deletes orphaned transactions in the partner split account, which don't have a 
corresponding transaction in the user split account any more. It does return a list with the deleted transactions. 
By default, the function compares transactions of the last 30 days. Optionally it takes a `since` parameter in the 
form of `datetime.date` to set a timeframe different from 30 days.

```py
ynab_split_budget.delete_orphans()
```
### Show Logs
The library logs information about the result of the methods at the 'INFO' level. The logs can be made visible by 
importing the logging module and set it to the level `INFO`. The logger itself can also be accessed via the `logger` 
attribute of the instance.
```py
import logging

logging.basicConfig(level='INFO')
```
### Run via bash commands
You can run this package also from bash with the following commands
```bash
$ python -m ynabsplitbudget -c <path/config.yaml#user_name> -s | --split-transactions
$ python -m ynabsplitbudget -c <path/config.yaml#user_name> -i | --insert-complements [-d | --since-date "YYYY-mm-dd"]
$ python -m ynabsplitbudget -c <path/config.yaml#user_name> -b | --check-balances
```
