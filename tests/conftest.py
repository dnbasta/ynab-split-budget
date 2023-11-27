import string
import random
import typing
from typing import get_type_hints
from unittest.mock import MagicMock

import pytest
import os


@pytest.fixture
def prod_conf_path():
	return f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/config.yaml'


def random_str() -> str:
	return ''.join(random.choices(string.ascii_lowercase, k=5))


def random_int() -> int:
	return random.randint(0, 1000)


def random_float() -> float:
	return random_int() / 100


def mock_dataclass(class_type: type) -> MagicMock:
	return MagicMock(spec=class_type(**get_type_hints(class_type)))


def create_mock_object(class_type: type, attr: dict = None):

	th = get_type_hints(class_type)
	for k, v in th.items():
		if v == str:
			th[k] = random_str()
		elif v == int:
			th[k] = random_int()
		elif v == float:
			th[k] = random_float()
		elif typing.get_origin(v) == typing.Union:
			th[k] = create_mock_object(next(t for t in typing.get_args(v)))
		else:
			th[k] = create_mock_object(v)

	if attr is not None:
		for k, v in attr.items():
			th[k] = v

	return class_type(**th)


@pytest.fixture
def mock_transaction_dict():
	return {'id': 'sample_id',
			'memo': 'sample_memo',
			'payee_name': 'sample_payee',
			'deleted': False,
			'account_id': 'sample_account',
			'amount': 10,
			'date': '2023-10-01',
			'cleared': 'cleared',
			'import_id': None}


@pytest.fixture
def mock_budget():
	return {'id': 'sample_budget_id',
			'name': 'sample_budget_name',
			'currency_format': {'iso_code': 'sample_iso_code'},
			'accounts': [{'id': 'sample_account_id',
			   		      'name': 'sample_account_name',
						  'deleted': False,
						  'transfer_payee_id': 'sample_transfer_payee_id'}],
															 }