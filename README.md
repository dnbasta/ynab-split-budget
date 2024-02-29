# ynab-split-budget

[![GitHub Release](https://img.shields.io/github/release/dnbasta/ynab-split-budget?style=flat)]() 
[![Github Release](https://img.shields.io/maintenance/yes/2100)]()

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

## Create config
Create a config `dict` with the below structure. 
```py
CONFIG = {
    '<user_name>': {
        'budget': '<budget_id>',
        'account': '<account_id>',
        'token': '<ynab_token>',
        'flag': '<color>'},
    '<partner_name>': {
        'budget': '<budget_id>',
        'account': '<account_id>',
        'token': '<ynab_token>',
        'flag': '<color>'}
}
```
You can find the ID of the budget and of the account if you go to https://app.ynab.com/ and open the target account by
clicking on the name on the left hand side menu. The URL does now contain both IDs 
`https://app.ynab.com/<budget_id>/accounts/<account_id>`
Possible colors for the flag value are `red`, `orange`, `yellow`, `green`, `blue` and `purple`

Alternatively you can save the config in a yaml file with the below structure and provide the path to the library 
when initializing
```yaml
<user_name>:
  token: <ynab_token>
  budget: <budget_id>
  account: <account_id>
  flag: <color>
<partner_name>:
  token: <ynab_token>
  budget: <budget_id>
  account: <account_id>
  flag: <color>
```

## Usage
### 1. Create a transaction
Create a transaction in your budget and add the defined color flag. Only cleared transactions will be considered. 
By default, the transaction will be split in half, but you can specify a different split by adding `@x%` for 
percentage or `@x` for specific amount in the memo of the transaction. The amount you specify in this split will be 
transferred to your sharing account. You can also create a plain transfer to the shared account which will be 
completely allocated to the partner account.
### 2. Initialize and run the split functionality

```py
from ynabsplitbudget import YnabSplitBudget

# initialize from config dict
ynab_split_budget = YnabSplitBudget(config=CONFIG, user='<user_name>')
# or alternatively from yaml
ynab_split_budget = YnabSplitBudget.from_yaml(path='path/to/config.yaml', user='<user_name')

ynab_split_budget.split_transactions()
```
### 3. Clear the newly split transaction
Using the YNAB web interface go to your split account and clear the newly split transaction over there. This can 
currently not be automated as YNAB API can't clear split transactions at this point in time.
### 4. Run the insert functionality
By default the library will compare and insert transactions of the last 30 days. If you would like to do it for a 
different timeframe you can provide a `since` argument to the function with a value from `datetime.date`
```py
ynab_split_budget.insert_complements()
```
## Advanced Usage
### Check Balances
Additionally you can check if the cleared balances in both accounts match. If they don't match you will get back a 
`BalancesDontMatch` Error which also gives you the two values of the balances.
```py
ynab_split_budget.raise_on_balances_off()
```
### Delete Orphaned Complements
If you delete a transaction in your share account you can use this function to delete the respective complement on 
your partners shared account. It does return a list with the deleted transactions. By default the library will 
compare transactions of the last 30 days. If you would like to do it for a different timeframe you can provide a 
`since` argument to the function with a value from `datetime.date`
```py
ynab_split_budget.delete_orphaned_complements()
```
### Show Logs
The library logs information about the result of the methods on the 'INFO' level. If you want to see these logs 
import the logging module and set it to the level `INFO`. You can also access the logger for advanced configuration 
via the `logger` attribute of your `YnabSplitBudget`instance.
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
