from pathlib import Path

import yaml


class FileLoader:

	def __init__(self, path: str):
		self._path = path

	def load(self) -> dict:
		with Path(self._path).open(mode='r') as f:
			config_dict = yaml.safe_load(f)
			return config_dict
