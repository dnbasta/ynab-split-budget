from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class BaseAccount:
	budget_id: str
	budget_name: str
	account_id: str
	account_name: str
	transfer_payee_id: str
	currency: str


@dataclass(eq=True, frozen=True)
class Account(BaseAccount):
	server_knowledge: int

	@classmethod
	def from_base_account(cls, base_account: BaseAccount, server_knowledge):
		return cls(budget_id=base_account.budget_id,
				   account_id=base_account.account_id,
				   transfer_payee_id=base_account.transfer_payee_id,
				   server_knowledge=server_knowledge,
				   budget_name=base_account.budget_name,
				   account_name=base_account.account_name,
				   currency=base_account.currency)

