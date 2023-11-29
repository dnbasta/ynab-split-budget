from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class FlagSplit:
	color: str
	split: float
