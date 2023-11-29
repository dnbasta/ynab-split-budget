from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class Category:
	id: str
	name: str
