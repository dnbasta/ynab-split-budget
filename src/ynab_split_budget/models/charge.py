from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.ynab_split_budget.config import User
from src.ynab_split_budget.models.operations import Operation
from src.ynab_split_budget.models.transaction import Category


@dataclass(eq=True, frozen=True)
class Charge:
    id: str
    charge_date: date
    memo: str
    payee_name: str
    owner_owed: Optional[float]
    recipient_owed: Optional[float]
    paid: float
    owner: User
    owner_transaction_id: str
    owner_category: Category
    recipient: User


@dataclass(eq=True, frozen=True)
class ChargeOperation:
    charge: Charge
    user_1_operation: Optional[Operation]
    user_2_operation: Optional[Operation]

    def __repr__(self):
        r = ' | '.join([str(self.charge.owner.name),
                        str(self.charge.__class__.__name__),
                        f'{self.charge.charge_date:%Y-%m-%d}',
                        str(self.charge.paid),
                        str(self.charge.payee_name)])
        return r


@dataclass(eq=True, frozen=True)
class ChargeNew(Charge):
    pass


@dataclass(eq=True, frozen=True)
class ChargeNewIncompleteRecipient(Charge):
    pass


@dataclass(eq=True, frozen=True)
class ChargeNewIncompleteRecipient(Charge):
    pass


@dataclass(eq=True, frozen=True)
class ChargeNewIncompleteOwner(Charge):
    recipient_transaction_id: str


@dataclass(eq=True, frozen=True)
class ChargeChanged(Charge):
    recipient_transaction_id: str


@dataclass(eq=True, frozen=True)
class ChargeOwnerDeleted(Charge):
    owner_transaction_id: Optional[str]
    paid: Optional[float]
    recipient_transaction_id: str


@dataclass(eq=True, frozen=True)
class ChargeRecipientDeleted(Charge):
    recipient_transaction_id: str


