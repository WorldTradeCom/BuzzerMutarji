from Source.Core.Translator import TranslationModes, Translator
from Source.Core.UserProperties import UserProperties
from Source.UI.Keyboards import InlineKeyboards

from dublib.TelebotUtils import TeleCache, TeleMaster, UserData, UsersManager
from dublib.Methods.Filesystem import ReadTextFile
from dublib.Engine.Bus import ExecutionStatus

from os import PathLike
from time import sleep

from telebot import TeleBot, types
import requests

def AnswerToObscene(bot: TeleBot, user: UserData):
	"""
	Отправляет ответ на нецензурные выражения.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param user: Данные пользователя.
	:type user: UserData
	"""

	Delay = 0.75
	Messages = (
		"🤦‍♂️",
		"Камон, ты реально такое спрашиваешь?",
		"Капец, ты инцел!"
	)

	for Index in range(len(Messages)):
		bot.send_message(user.id, Messages[Index])
		if Index < len(Messages) - 1: sleep(Delay)

def CheckBlacklist(message: str, bot: TeleBot, cacher: TeleCache, user: UserData, autosend: bool = True) -> ExecutionStatus:
	"""
	Проверяет, соответствует ли текст сообщения строке из чёрного списка. Если соответствует, автоматически отправляет соответствующее сообщение.

	:param message: Текст сообщения.
	:type message: str
	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param cacher: Менеджер кэша.
	:type cacher: TeleCache
	:param user: Данные пользователя.
	:type user: User
	:param autosend: Указывает, нужно ли отправлять сообщение с требованием подписки.
	:type autosend: bool
	:return: Состояние: соответствует ли текст строке из чёрного списка. Под ключом _sended_ находится состояние отправки сообщения.
	:rtype: ExecutionStatus
	"""

	Blacklist = ReadTextFile("Data/Materials/Text/blacklist_strings.txt", split = True, strip = True)
	Status = ExecutionStatus()
	Status.value = False
	Status["sended"] = False

	for String in message.split("\n"):
		if String in Blacklist: Status.value = True

	if Status and autosend:
		bot.send_animation(
			chat_id = user.id,
			animation = cacher.get_real_cached_file("Data/Materials/Animation/bad.mp4", autoupload_type = types.InputMediaAnimation).file_id,
			caption = "<b><i>" + "- Чел, ну реально! Не пазорься!" + "</i></b>",
			parse_mode = "HTML",
			reply_markup = InlineKeyboards.Delete("Был не прав, признаю!")
		)
		Status["sended"] = True

	return Status

def CheckMessageLength(bot: TeleBot, user: UserData, message: str) -> bool:
	"""
	Проверяет, вышел ли пользователь за лимит длины сообщения.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param user: Данные пользователя.
	:type user: UserData
	:param message: Текст сообщения.
	:type message: str
	:return: Возвращает `True` при превышении лимита.
	:rtype: bool
	"""

	MAX_LENGTH = 1024
	MessageLength = len(message)

	if MessageLength > MAX_LENGTH:
		bot.send_message(
			chat_id = user.id,
			text = f"Слишком длинное сообщение для перевода. Сократите до {MAX_LENGTH} символа. У вас сейчас {MessageLength} символов",
			parse_mode = "HTML",
			reply_markup = InlineKeyboards.Delete("Понял! Ща!")
		)
		return True
	
	return False

def CheckPointsLimit(bot: TeleBot, user: UserData) -> bool:
	"""
	Проверяет, вышел ли пользователь за лимит количества переводов.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param user: Данные пользователя.
	:type user: UserData
	:return: Возвращает `True` при превышении лимита.
	:rtype: bool
	"""

	Properties = UserProperties(user)

	if not Properties.is_points_available():
		ReferalLink = "https://t.me/" + bot.get_me().username + f"?start={user.id}"
		Text = (
			"Лимит перевода для вас на сегодня исчерпан. Вы можете делать по 3 перевода в день. Чтобы увеличить лимит переводов, пригласите, пожалуйста, друга.",
			"Вот ваша ссылка приглашение поделитесь ею:" + f" <code>{ReferalLink}</code>"
		)
		bot.send_message(chat_id = user.id, text = "\n\n".join(Text), parse_mode = "HTML")
		return True
	
	return False

def CheckSubscription(master: TeleMaster, cacher: TeleCache, user: UserData, subscriptions: dict[str, dict], autosend: bool = True) -> ExecutionStatus:
	"""
	Проверяет, выполнил ли пользователь условия подписки.

	:param master: Мастер-бот.
	:type master: MasterBot
	:param cacher: Менеджер кэша.
	:type cacher: TeleCache
	:param user: Данные пользователя.
	:type user: User
	:param subscriptions: Словарь с данными необходимых подписок, где ключ – название кнопки, а в словаре-значении имеется два поля: _id_ и _link_.
	:type subscriptions: dict[str, dict]
	:param autosend: Указывает, нужно ли отправлять сообщение с требованием подписки.
	:type autosend: bool
	:return: Состояние: выполнены ли условия подписки. Под ключом _sended_ находится состояние отправки сообщения.
	:rtype: ExecutionStatus
	"""

	Status = ExecutionStatus()
	Status.value = master.check_user_subscriptions(user, tuple(subscriptions[Key]["id"] for Key in subscriptions.keys()))
	Status["sended"] = False

	Caption = (
		"<b><i>" + "Для пользования этим ботом подпишись на наш новостной канал и на послания!" + "</i></b> 💋\n",
		"Как подпишешься, дави на кнопку \"Я подписался!\""
	)
	
	if Status.value == False and autosend:
		master.bot.send_animation(
			chat_id = user.id,
			animation = cacher.get_real_cached_file("Data/Materials/Animation/subscribe.mp4", autoupload_type = types.InputMediaAnimation).file_id,
			caption = "\n".join(Caption),
			parse_mode = "HTML",
			reply_markup = InlineKeyboards.Subscribe(subscriptions)
		)
		Status["sended"] = True
		
	return Status

def DownloadFile(url: str, path: PathLike) -> bool:
	"""
	Скачивает файл по ссылке.

	:param url: Ссылка на файл.
	:type url: str
	:param path: Путь к файлу.
	:type path: PathLike
	:return: Возвращает `True`, если файл успешно скачан.
	:rtype: bool
	"""

	try:
		Response = requests.get(url)
		with open(path, "wb") as FileWriter: FileWriter.write(Response.content)
		return True
	
	except: return False

def ProcessReferalLink(bot: TeleBot, users_manager: UsersManager, user: UserData, message: str) -> bool:
	"""
	Обрабатывает переход по реферальной ссылке.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param users_manager: Менеджер пользователей.
	:type users_manager: UsersManager
	:param user: Данные пользователя.
	:type user: UserData
	:param message: Текст сообщения.
	:type message: str
	:return: Возвращает `True`, если был обработан переход по реферальной ссылке.
	:rtype: bool
	"""

	MessageParts = message.split()
	if len(MessageParts) != 2 or MessageParts[0] != "/start" or not MessageParts[1].isdigit(): return False
	InviterID = int(MessageParts[1])

	if users_manager.is_user_exists(InviterID):
		user.set_property("invited_by", InviterID)
		Inviter = users_manager.get_user(InviterID)
		InviterProperties = UserProperties(Inviter)
		Inviter.suppress_saving(True)
		InviterProperties.add_invited_user(user.id)
		InviterProperties.add_bonus_points(5)
		Inviter.suppress_saving(False, save = True)

		bot.send_message(
			chat_id = InviterID,
			text = "От вас пришел кореш! С нас 5 бонусных переводов!",
			reply_markup = InlineKeyboards.Delete("Вот это ништяк!")
		)

def SendModeSwitcher(bot: TeleBot, user: UserData):
	"""
	Отправляет переключатель режима перевода.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param user: Данные пользователя.
	:type user: UserData
	"""

	bot.send_message(
		chat_id = user.id,
		text = "Выберите, какой режим перевода интересует:",
		reply_markup = InlineKeyboards.Switcher(user)
	)

def SendShareMessage(bot: TeleBot, cacher: TeleCache, user: UserData):
	"""
	Отправляет сообщение для рекламной пересылки.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param cacher: Менеджер кэша.
	:type cacher: TeleCache
	:param user: Данные пользователя.
	:type user: UserData
	"""

	Username = "@" + bot.get_me().username
	Text = (
		"\n".join((Username,) * 3) + "\n",
		"<b>" + "Переводчик с зумерского | Пикми, чечик, найк про" + "</b>",
		"Как раз то, что ты искал!" + "\n",
		"<b><i>" + "Пользуйся и делись с друзьями!" + "</i></b>"
	)
	
	bot.send_photo(
		chat_id = user.id,
		photo = cacher.get_real_cached_file("Data/Materials/Photo/share.jpg", autoupload_type = types.InputMediaPhoto).file_id,
		caption = "\n".join(Text),
		parse_mode = "HTML",
		reply_markup = InlineKeyboards.Share(Username)
	)

def TranslateText(bot: TeleBot, user: UserData, translator: "Translator", text: str):
	"""
	Обрабатывает перевод текста.

	:param bot: Бот Telegram.
	:type bot: TeleBot
	:param user: Данные пользователя.
	:type user: UserData
	:param text: Текст для перевода.
	:type text: str
	"""

	Result = translator.translate(mode = TranslationModes(user.get_property("mode")), text = text)

	if Result:
		Properties = UserProperties(user)
		Properties.subtract_point()

	else:
		bot.send_message(
			chat_id = user.id,
			text = "Ууупс… Не удалось выполнить перевод."
		)