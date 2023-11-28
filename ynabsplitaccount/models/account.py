from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class Account:
	budget_id: str
	budget_name: str
	account_id: str
	account_name: str
	transfer_payee_id: str
	currency: str

