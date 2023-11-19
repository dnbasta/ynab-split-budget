from abc import ABC
from dataclasses import dataclass
from datetime import date

from src.ynabsplitbudget.config import User


@dataclass(eq=True, frozen=True)
class Operation(ABC):
    owner: User

    def as_dict(self):
        return None


@dataclass(eq=True, frozen=True)
class OperationInsert(Operation):
    amount: float
    date: date
    payee: str
    hashed_id: str
    memo: str

    def as_dict(self) -> dict:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "amount": int(self.amount * 1000),
            "payee_name": self.payee,
            "memo": self.memo,
            "cleared": 'cleared',
            "approved": False,
            "import_id": f's||{self.hashed_id}-0'
        }


@dataclass(eq=True, frozen=True)
class OperationSplit(Operation):
    id: str
    paid: float
    owed: float
    payee: str
    category_id: str
    memo: str

    def as_dict(self) -> dict:
        return {"cleared": "cleared",
                "subtransactions":
                    [{
                        "amount": round(-int((self.paid - self.owed) * 1000), -1),
                        "memo": self.memo,
                        "payee_id": self.owner.split_transfer_payee_id,
                        "cleared": 'cleared',
                     },
                     {
                        "amount": round(-int(self.owed * 1000), -1),
                        "memo": self.memo,
                        "category_id": self.category_id,
                        "payee_name": self.payee,
                        "cleared": 'cleared',
                     }]
                }


@dataclass(eq=True, frozen=True)
class OperationUpdate(Operation):
    id: str
    amount: float
    date: date
    memo: str
    payee: str

    def as_dict(self) -> dict:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "amount": int(self.amount * 1000),
            "memo": self.memo,
            "payee_name": self.payee,
            "cleared": 'cleared',
            "approved": False
        }


@dataclass(eq=True, frozen=True)
class OperationDelete(Operation):
    id: str

