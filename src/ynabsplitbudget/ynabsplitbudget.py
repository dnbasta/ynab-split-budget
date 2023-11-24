from dataclasses import dataclass
from typing import List, Optional

from src.ynabsplitbudget.builders.configbuilder import ConfigBuilder
from src.ynabsplitbudget.client import TransactionClient, KnowledgeClient
from src.ynabsplitbudget.models.charge import Charge
from src.ynabsplitbudget.models.config import Config, ConfigMissingKnowledge
from src.ynabsplitbudget.models.exception import NoServerKnowledge
from src.ynabsplitbudget.models.operations import Operation
from src.ynabsplitbudget.repositories.baserepository import BaseRepository
from src.ynabsplitbudget.repositories.chargeoperationrepository import ChargeOperationRepository


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
                                 server_knowledge=charge_ops_repo.user_1_server_knowledge)
        user_2 = FetchResultUser(charges=charge_ops_repo.user_2_charges,
                                 operations=charge_ops_repo.user_2_ops,
                                 name=charge_ops_repo.user_2.name,
                                 server_knowledge=charge_ops_repo.user_2_server_knowledge)
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


class YnabSplitBudget:
    _config: Optional[Config]

    def load_config(self, path: str):
        config = ConfigBuilder(path=path).build_from_path()
        self._config = config
        print(f"loaded config from {path}")

    def update_server_knowledge(self):
        u1_knowledge = KnowledgeClient(token=self._config.user_1.token,
                                    account=self._config.user_1.account).fetch_server_knowledge()
        u2_knowledge = KnowledgeClient(token=self._config.user_2.token,
                                    account=self._config.user_2.account).fetch_server_knowledge()
        self._update_server_knowledge(user_1=u1_knowledge, user_2=u2_knowledge)

    def fetch_charges(self) -> FetchResult:
        if isinstance(self._config, ConfigMissingKnowledge):
            raise NoServerKnowledge(self._config)
        base_repo = BaseRepository.from_config(config=self._config)
        charge_ops_repo = ChargeOperationRepository.from_config(base_repo=base_repo, config=self._config)
        fetch_result = FetchResult.from_charge_ops_repo(charge_ops_repo=charge_ops_repo)
        print(f'fetched {fetch_result.user_1.count} charges from {fetch_result.user_1.name} and '
              f'{fetch_result.user_2.count} from {fetch_result.user_2.name}')
        return fetch_result

    def process_charges(self, fetch_result: FetchResult):

        user_1_client = TransactionClient.from_user(user=self._config.user_1)
        user_2_client = TransactionClient.from_user(user=self._config.user_2)

        [user_1_client.process_operation(o) for o in fetch_result.user_1.operations]
        [user_2_client.process_operation(o) for o in fetch_result.user_2.operations]

        # log processed and return
        r = ProcessResponse(user_1_owned_processed=fetch_result.user_1.count,
                            user_2_owned_processed=fetch_result.user_2.count,
                            user_1_balance=user_1_client.fetch_balance(),
                            user_2_balance=user_2_client.fetch_balance())
        print(f"processed {r.user_1_owned_processed} for {self._config.user_1.name} "
              f"(balance {r.user_1_balance} {self._config.user_1.account.currency}) "
              f"and {r.user_2_owned_processed} for {self._config.user_2.name} "
              f"(balance {r.user_2_balance} {self._config.user_2.account.currency})")

        self._update_server_knowledge(user_1=fetch_result.user_1.server_knowledge,
                                     user_2=fetch_result.user_2.server_knowledge)
        return r

    def _update_server_knowledge(self, user_1: int, user_2: int) -> None:
        cb = ConfigBuilder(path=self._config.path)
        new_config = cb.build_from_config(config=self._config,
                                      user_1_server_knowledge=user_1,
                                      user_2_server_knowledge=user_2)
        print(f'server knowledge: '
              f'{new_config.user_1.name}: {new_config.user_1.account.server_knowledge}, '
              f'{new_config.user_2.name}: {new_config.user_2.account.server_knowledge}')
        new_config.save()
        self._config = new_config

