from dataclasses import dataclass
from typing import List

from src.ynab_split_budget.client import Client
from src.ynab_split_budget.models.charge import ChargeOperation
from src.ynab_split_budget.repositories.baserepository import BaseRepository
from src.ynab_split_budget.repositories.chargeoperationrepository import ChargeOperationRepository
from src.ynab_split_budget.config import Config, ServerKnowledge


@dataclass
class FetchResult:
    _charge_ops_repo: ChargeOperationRepository

    @property
    def charges(self) -> List[ChargeOperation]:
        return self._charge_ops_repo.charges

    @property
    def server_knowledge_user_1(self) -> int:
        return self._charge_ops_repo.server_knowledge.user_1

    @property
    def server_knowledge_user_2(self) -> int:
        return self._charge_ops_repo.server_knowledge.user_2

    @property
    def user_1_count(self) -> int:
        return self._charge_ops_repo.user_1_owned

    @property
    def user_2_count(self) -> int:
        return self._charge_ops_repo.user_2_owned

    @property
    def user_1_name(self) -> str:
        return self._charge_ops_repo.user_1.name

    @property
    def user_2_name(self) -> str:
        return self._charge_ops_repo.user_2.name


@dataclass
class ProcessResponse:
    user_1_owned_processed: int
    user_2_owned_processed: int
    balance_off_by: bool


@dataclass
class YnabSplitBudget:
    _config: Config
    _path: str

    @classmethod
    def from_config(cls, path: str):
        return cls(_config=Config.from_path(path=path),
                   _path=path)

    def fetch_charges(self) -> FetchResult:
        base_repo = BaseRepository.from_config(config=self._config)
        charge_ops_repo = ChargeOperationRepository.from_config(base_repo=base_repo, config=self._config)
        return FetchResult(_charge_ops_repo=charge_ops_repo)

    def process_charges(self, fetch_result: FetchResult):

        user_1_client = Client.from_config(user=self._config.user_1,
                                           last_server_knowledge=self._config.last_server_knowledge.user_1)
        user_2_client = Client.from_config(user=self._config.user_2,
                                           last_server_knowledge=self._config.last_server_knowledge.user_2)

        [user_1_client.process_operation(o.user_1_operation) for o in fetch_result.charges if o.user_1_operation is not None]
        [user_2_client.process_operation(o.user_2_operation) for o in fetch_result.charges if o.user_2_operation is not None]

        self.update_server_knowledge(user_1=fetch_result.server_knowledge_user_1,
                                     user_2=fetch_result.server_knowledge_user_2)

        # log processed and return
        r = ProcessResponse(user_1_owned_processed=fetch_result.user_1_count,
                            user_2_owned_processed=fetch_result.user_2_count,
                            balance_off_by=user_1_client.fetch_balance() - user_2_client.fetch_balance())
        print(r.__dict__)
        return r

    def update_server_knowledge(self, user_1: int, user_2: int) -> None:
        sk = ServerKnowledge(user_1=user_1, user_2=user_2)
        sk.to_file(self._path)
