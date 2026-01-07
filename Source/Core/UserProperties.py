from Source.Core.Translator.Structs import TranslationModes

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from dublib.TelebotUtils.Users import UserData

class UserProperties:
	"""Абстракция свойств пользователя."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def bonus_points(self) -> int:
		"""Количество бонусных очков перевода."""

		return self.__User.get_property("bonus_points")

	@property
	def daily_points(self) -> int:
		"""Количество ежедневных очков перевода."""

		return self.__User.get_property("daily_points")

	@property
	def invited_by(self) -> int | None:
		"""ID пригласившего пользователя."""

		return self.__User.get_property("invited_by")
	
	@property
	def invited_users(self) -> tuple[int]:
		"""Последовательность ID приглашённых пользователей."""

		return tuple(self.__User.get_property("invited_users"))

	@property
	def translation_mode(self) -> TranslationModes:
		"""Режим перевода."""

		return TranslationModes(self.__User.get_property("mode"))

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, user: "UserData"):
		"""
		Абстракция свойств пользователя.

		:param user: Данные пользователя.
		:type user: UserData
		"""

		self.__User = user

	def add_invited_user(self, user_id: int):
		"""
		Добавляет ID приглашённого пользователя.

		:param user_id: ID приглашённого пользователя.
		:type user_id: int
		"""

		InvitedUsers: list[str] = self.__User.get_property("invited_users", copy = False)
		InvitedUsers.append(user_id)

	def add_bonus_points(self, points: int):
		"""
		Добавляет бонусные очки.

		:param points: Количество бонусных очков.
		:type points: int
		"""

		self.__User.set_property("bonus_points", self.bonus_points + points)

	def is_points_available(self) -> bool:
		"""
		Проверяет, есть ли у пользователя хотя бы одно очко.

		:return: Возвращает `True` при наличии очка.
		:rtype: bool
		"""

		return bool(self.bonus_points + self.daily_points)

	def set_daily_points(self, points: int):
		"""
		Устанавливает количество ежедневных очков пользователя.

		:param points: Количество ежедневных очков.
		:type points: int
		"""

		self.__User.set_property("dailty_points", points)

	def set_inviter(self, inviter_id: int):
		"""
		Задаёт ID пригласившего пользователя.

		:param inviter_id: ID пригласившего пользователя.
		:type inviter_id: int
		:raise ValueError: Выбрасывается, если ID пригласившего уже задан.
		"""

		if self.invited_by: raise ValueError("Inviter ID already setted.")
		self.__User.set_property("invited_by", inviter_id)

	def subtract_point(self):
		"""Отнимает у мользователя очко."""

		if self.daily_points: self.__User.set_property("daily_points", self.daily_points - 1)
		elif self.bonus_points: self.__User.set_property("bonus_points", self.bonus_points - 1)