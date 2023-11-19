from dataclasses import dataclass
from typing import List

from src.ynabsplitbudget.client import Client
from src.ynabsplitbudget.models.charge import Charge
from src.ynabsplitbudget.models.operations import Operation
from src.ynabsplitbudget.repositories.baserepository import BaseRepository
from src.ynabsplitbudget.repositories.chargeoperationrepository import ChargeOperationRepository
from src.ynabsplitbudget.config import Config, ServerKnowledge


@dataclass
class FetchResultUser:
    charges: List[Charge]
    name: str
    server_knowledge: int
    operations: List[Operation]

    @property
    def count(self):
        return len(self.charges)


@dataclass
class FetchResult:
    user_1: FetchResultUser
    user_2: FetchResultUser

    @classmethod
    def from_charge_ops_repo(cls, charge_ops_repo: ChargeOperationRepository):
        user_1 = FetchResultUser(charges=charge_ops_repo.user_1_charges,
                                 operations=charge_ops_repo.user_1_ops,
                                 name=charge_ops_repo.user_1.name,
                                 server_knowledge=charge_ops_repo.server_knowledge.user_1)
        user_2 = FetchResultUser(charges=charge_ops_repo.user_2_charges,
                                 operations=charge_ops_repo.user_2_ops,
                                 name=charge_ops_repo.user_2.name,
                                 server_knowledge=charge_ops_repo.server_knowledge.user_2)
        return cls(user_1=user_1, user_2=user_2)


@dataclass
class ProcessResponse:
    user_1_owned_processed: int
    user_2_owned_processed: int
    user_1_balance: float
    user_2_balance: float

    @property
    def balance_matches(self) -> bool:
        if self.user_1_balance - self.user_2_balance == 0:
            return True
        return False


@dataclass
class YnabSplitBudget:
    _config: Config
    _path: str

    @classmethod
    def from_config(cls, path: str = ''):
        return cls(_config=Config.from_path(path=path),
                   _path=path)

    def fetch_charges(self) -> FetchResult:
        base_repo = BaseRepository.from_config(config=self._config)
        charge_ops_repo = ChargeOperationRepository.from_config(base_repo=base_repo, config=self._config)
        return FetchResult.from_charge_ops_repo(charge_ops_repo=charge_ops_repo)

    def process_charges(self, fetch_result: FetchResult):

        user_1_client = Client.from_config(user=self._config.user_1,
                                           last_server_knowledge=self._config.last_server_knowledge.user_1)
        user_2_client = Client.from_config(user=self._config.user_2,
                                           last_server_knowledge=self._config.last_server_knowledge.user_2)

        [user_1_client.process_operation(o) for o in fetch_result.user_1.operations]
        [user_2_client.process_operation(o) for o in fetch_result.user_2.operations]

        self.update_server_knowledge(user_1=fetch_result.user_1.server_knowledge,
                                     user_2=fetch_result.user_2.server_knowledge)

        # log processed and return
        r = ProcessResponse(user_1_owned_processed=fetch_result.user_1.count,
                            user_2_owned_processed=fetch_result.user_2.count,
                            user_1_balance=user_1_client.fetch_balance(),
                            user_2_balance=user_2_client.fetch_balance())
        print(r.__dict__)
        return r

    def update_server_knowledge(self, user_1: int, user_2: int) -> None:
        sk = ServerKnowledge(user_1=user_1, user_2=user_2)
        print(f'new server knowledge: {sk.__dict__}')
        sk.to_file(self._path)