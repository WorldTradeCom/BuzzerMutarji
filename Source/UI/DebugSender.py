from Source.Core.UserProperties import UserProperties

from typing import Any, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
	from dublib.TelebotUtils.Users import UserData

	from telebot import TeleBot

class DebugSender:
	"""Оператор отправки отладочного сообщения."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __FormatBool(self, label: str, value: bool) -> str:
		"""
		Форматирует логическое значение для отправки.

		:param label: Надпись-идентификатор.
		:type label: str
		:param value: Значение.
		:type value: bool
		:return: Строка сообщения.
		:rtype: str
		"""
		
		value = str(value).lower()
		
		return self.__FormatStr(label, value)

	def __FormatInt(self, label: str, value: int) -> str:
		"""
		Форматирует целочисленное значение для отправки.

		:param label: Надпись-идентификатор.
		:type label: str
		:param value: Значение.
		:type value: int
		:return: Строка сообщения.
		:rtype: str
		"""

		if type(value) == int: value = f"<b>{value}</b>"
		else: value = "<i>null</i>"
		
		return f"{label}: {value}"
	
	def __FormatSequence(self, label: str, sequence: Iterable[Any]) -> str:
		"""
		Форматирует последовательность для отправки.

		:param label: Надпись-идентификатор.
		:type label: str
		:param sequence: Последовательность.
		:type sequence: Iterable[Any]
		:return: Строка сообщения.
		:rtype: str
		"""

		Elements = "<i>null</i>"

		if sequence:
			Elements = tuple(str(Value) for Value in sequence)
			Elements = ", ".join(Elements)

		return f"{label}: {Elements}"

	def __FormatStr(self, label: str, value: str) -> str:
		"""
		Форматирует строковое значение для отправки.

		:param label: Надпись-идентификатор.
		:type label: str
		:param value: Значение.
		:type value: str
		:return: Строка сообщения.
		:rtype: str
		"""
		
		if not value: value = "null"
		
		return f"{label}: <i>{value}</i>"

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, bot: "TeleBot", user: "UserData"):
		"""
		Оператор отправки отладочного сообщения.
		
		:param bot: Бот Telegram.
		:type bot: TeleBot
		:param user: Данные пользователя.
		:type user: UserData
		"""

		self.__Bot = bot
		self.__User = user

		self.__Properties = UserProperties(user)

	def send(self):
		"""Отправляет отладочное сообщение."""


		Text = (
			"<b>" + "Данные отладки" + "</b>",
			f"Ваш ID: <code>{self.__User.id}</code>\n",
			self.__FormatInt("Ежедневные очки", self.__Properties.daily_points),
			self.__FormatInt("Бонусные очки", self.__Properties.bonus_points),
			"",
			self.__FormatBool("Статус генерации", self.__User.check_flags("in-generation")),
			self.__FormatStr("Режим", self.__Properties.translation_mode.value),
			"",
			self.__FormatInt("Приглашён", self.__Properties.invited_by),
			self.__FormatSequence("Пригласил", self.__Properties.invited_users)
		)

		self.__Bot.send_message(
			chat_id = self.__User.id,
			text = "\n".join(Text),
			parse_mode = "HTML"
		)