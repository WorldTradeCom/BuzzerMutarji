from .Structs import NeuroHubOptions, TranslationModes

from Source.NeuroHub.Connection.API import Options, Requestor

from dublib.CLI.Templates.Bus import PrintError
from dublib.Engine.Bus import ExecutionStatus

from typing import Literal

class Translator:
	"""Русско-зумерский переводчик."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __GetRequest(self, mode: TranslationModes, additional: str | None = None) -> str:
		"""
		Возвращает текст запроса к нейросети в зависимости от режима перевода.

		:param mode: Режим перевода.
		:type mode: TranslationModes
		:param additional: Дополнительная строка запроса.
		:type additional: str | None
		:return: Текст запроса.
		:rtype: str
		"""

		Request = [
			"Сохрани оригинальное форматирование, эмодзи и абзацы, если они есть, а также адаптируй и подставь HTML как в оригинале.",
			"Нe используй Markdown! Не добавляй ничего от себя!"
		]
		if additional: Request.append(additional)

		match mode:
			case TranslationModes.To: return " ".join(["Переведи следующий текст на зумерский язык."] + Request)
			case TranslationModes.From: return " ".join(["Переведи следующий текст с зумерского на литературный русский."] + Request)

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

	def translate(self, mode: TranslationModes, text: str, additional: str | None = None) -> ExecutionStatus:
		"""
		Переводит текст в выбранном режиме.

		:param mode: Режим перевода.
		:type mode: TranslationModes
		:param text: Текст для перевода.
		:type text: str
		:param additional: Дополнительная строка запроса.
		:type additional: str | None
		:return: Контейнер результата.
		:rtype: ExecutionStatus
		"""

		Settings = Options()
		Settings.select_source(self.__NeuroHubOptions.source)
		Settings.set_model(self.__NeuroHubOptions.model)
		Settings.set_force_proxy(self.__NeuroHubOptions.force_proxy)
		Master = Requestor(Settings, port = self.__NeuroHubOptions.port)
		Response = Master.generate(self.__GetRequest(mode, additional) + "\n" + text)

		Status = ExecutionStatus()
		Status.code = Response.status_code
		
		if Response.json:
			Status.value = Response.json.get("text")

			if not Status: 
				PrintError("Generation failed with response JSON:")
				print(Response.json)

		return Status