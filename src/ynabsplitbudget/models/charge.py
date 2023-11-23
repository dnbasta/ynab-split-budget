from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.ynabsplitbudget.models.transaction import Category
from src.ynabsplitbudget.models.user import User


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

    def __repr__(self):
        r = ' | '.join([str(self.owner.name),
                        f'{self.charge_date:%Y-%m-%d}',
                        str(self.paid),
                        str(self.payee_name)])
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


