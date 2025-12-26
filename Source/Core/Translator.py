from Source.NeuroHub.Connection.API import Options, Requestor

from dublib.Engine.Bus import ExecutionStatus

from dataclasses import dataclass
from typing import Literal
import enum

#==========================================================================================#
# >>>>> ДОПОЛНИТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

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

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Translator:
	"""Русско-зумерский переводчик."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __GetRequest(self, mode: TranslationModes) -> str:
		"""
		Возвращает текст запроса к нейросети в зависимости от режима перевода.

		:param mode: Режим перевода.
		:type mode: TranslationModes
		:return: Текст запроса.
		:rtype: str
		"""

		To = (
			"Переведи следующий текст на русский зумерский язык.",
			"Сохрани оригинальное форматирование и абзацы, если они есть. Не разбивай на отдельные строки.",
			"Не добавляй ничего от себя!"
		)
		From = (
			"Переведи следующий текст с зумерского на литературный русский.",
			"Сохрани оригинальное форматирование и абзацы, если они есть. Не разбивай на отдельные строки.",
			"Не добавляй ничего от себя!"
		)

		match mode:
			case TranslationModes.To: return " ".join(To)
			case TranslationModes.From: return " ".join(From)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Русско-зумерский переводчик."""

		self.__NeuroHubOptions = None

	def set_neurohub_options(self, port: int, source: Literal["g4f", "gemini"], model: str, force_proxy: bool):
		"""
		Задаёт опции [NeuroHub](https://github.com/DUB1401/NeuroHub).

		:param port: Порт общения.
		:type port: int
		:param source: Провайдер нейросети.
		:type source: Literal["g4f", "gemini"]
		:param model: Модель нейросети.
		:type model: str
		:param force_proxy: Указывает, нужно ли обязательно использовать прокси для запросов к нейросети.
		:type force_proxy: bool
		"""

		self.__NeuroHubOptions = NeuroHubOptions(port, source, model, force_proxy)

	def translate(self, mode: TranslationModes, text: str) -> ExecutionStatus:
		"""
		Переводит текст в выбранном режиме.

		:param mode: Режим перевода.
		:type mode: TranslationModes
		:param text: Текст для перевода.
		:type text: str
		:return: Контейнер результата.
		:rtype: ExecutionStatus
		"""

		Settings = Options()
		Settings.select_source(self.__NeuroHubOptions.source)
		Settings.set_model(self.__NeuroHubOptions.model)
		Settings.set_force_proxy(self.__NeuroHubOptions.force_proxy)
		Master = Requestor(Settings, port = self.__NeuroHubOptions.port)
		Response = Master.generate(self.__GetRequest(mode) + "\n" + text)

		Status = ExecutionStatus()
		Status.code = Response.status_code
		if Response.json: Status.value = Response.json.get("text")

		return Status