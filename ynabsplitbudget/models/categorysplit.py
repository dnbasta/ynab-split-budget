from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class CategorySplit:
	name: str
	split: float
