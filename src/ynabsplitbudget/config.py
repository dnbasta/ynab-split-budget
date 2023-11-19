from dataclasses import dataclass

import yaml


@dataclass
class ServerKnowledge:
    user_1: int
    user_2: int

    @classmethod
    def from_path(cls, path: str):
        with open(f'{path}last_server_knowledge.yaml', 'r') as f:
            k_dict = yaml.safe_load(f)
        return cls(user_1=k_dict['user_1'],
                   user_2=k_dict['user_2'])

    def to_file(self, path: str):
        with open(f'{path}last_server_knowledge.yaml', 'w') as f:
            yaml.safe_dump({'user_1': self.user_1, 'user_2': self.user_2}, f)


@dataclass(eq=True, frozen=True)
class User:
    budget: str
    token: str
    split_account: str
    split_transfer_payee_id: str
    name: str

    @classmethod
    def from_dict(cls, user_dict: dict):
        return cls(budget=user_dict['budget'],
                   split_account=user_dict['split_account'],
                   split_transfer_payee_id=user_dict['split_transfer_payee_id'],
                   token=user_dict['token'],
                   name=user_dict['name'])


@dataclass
class Config:
    user_1: User
    user_2: User
    last_server_knowledge: ServerKnowledge

    @classmethod
    def from_path(cls, path: str):
        with open(f'{path}config.yaml', 'r') as f:
            config_dict = yaml.safe_load(f)
            user_1 = User.from_dict(user_dict=config_dict['user_1'])
            user_2 = User.from_dict(user_dict=config_dict['user_2'])
            last_server_knowledge = ServerKnowledge.from_path(path=path)
        return cls(user_1=user_1, user_2=user_2, last_server_knowledge=last_server_knowledge)
