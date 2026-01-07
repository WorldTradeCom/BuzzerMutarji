from dataclasses import dataclass
from typing import Literal
import enum

@dataclass
class NeuroHubOptions:
	port: int
	source: Literal["g4f", "gemini"]
	model: str
	force_proxy: bool

class TranslationModes(enum.Enum):
	"""Направленности перевода русского на зумерский."""

	From = "from"
	To = "to"