from Source.Core.Materials import MaterialsValidator
from Source.UI.Keyboards import ReplyKeyboards
from Source.Core.Speecher import Speecher
from Source.TeleBotAdminPanel import Panel
from Source.UI.CLI import COMMANDS
from Source import Functions

from dublib.TelebotUtils import TeleCache, TeleMaster, UsersManager
from dublib.Methods.System import CheckPythonMinimalVersion, Clear
from dublib.Methods.Filesystem import MakeRootDirectories
from dublib.CLI.Terminalyzer import Terminalyzer
from dublib.Engine.Configurator import Config

import shutil
import os

from badwords import ProfanityFilter
from telebot import types
import telebot

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

Clear()
CheckPythonMinimalVersion(3, 10)
MakeRootDirectories("Data/Temp")

Settings = Config("Settings.json")
Settings.load()
Bot = telebot.TeleBot(Settings["bot_token"])
Master = TeleMaster(Bot)
UsersManagerObject = UsersManager("Data/Users")
Cacher = TeleCache()
Cacher.set_bot(Bot)
Cacher.set_chat_id(Settings["cache_chat_id"])
ProfanityFilterObject = ProfanityFilter()
ProfanityFilterObject.init(["ru", "en"])
AdminPanel = Panel(Bot, UsersManagerObject, Settings["password"])
SpeecherObject = Speecher(Settings["vosk_model"])

#==========================================================================================#
# >>>>> ОБРАБОТКА АРГУМЕНТОВ ЗАПУСКА <<<<< #
#==========================================================================================#

Analyzer = Terminalyzer()
Analyzer.helper.enable(True)
CommandData = Analyzer.check_commands(COMMANDS)

if CommandData and CommandData.name:
	Cased = True

	match CommandData.name:

		case "materials": MaterialsValidator().print_materials()
		case "translate": print("Not implemented.")
		case "validate": MaterialsValidator().validate()

		case _: Cased = False

	if Cased: exit()

#==========================================================================================#
# >>>>> ОБРАБОТКА КОМАНД <<<<< #
#==========================================================================================#

AdminPanel.decorators.commands()

@Bot.message_handler(commands = ["start"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	User.set_property("mode", "to", force = False)

	Caption = (
		"Хай, бро!" + " 👋",
		"Эта типа транслейтер с зумерского на нормисский и обратно. Чекни сам, это реально имба!" + "\n",
		"Приветствуем!" + " 👋",
		"Это переводчик с зумерского на нормальный и обратно.",
		"Отправляйте любую информацию и наслаждайтесь переводом!" + "\n",
		"<i>" + "Поддерживает голосовой ввод" + "</i>"
	)

	Bot.send_animation(
		chat_id = User.id,
		animation = Cacher.get_real_cached_file("Data/Materials/Animation/start.mp4", autoupload_type = types.InputMediaAnimation).file_id,
		caption = "\n".join(Caption),
		parse_mode = "HTML",
		reply_markup = ReplyKeyboards.Menu()
	)

#==========================================================================================#
# >>>>> ОБРАБОТКА ТЕКСТА <<<<< #
#==========================================================================================#

@Bot.message_handler(content_types = ["text"])
def Text(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	if AdminPanel.procedures.text(Bot, UsersManagerObject, Message): return
	Functions.CheckSubscription(Master, Cacher, User, Settings["subscriptions"])

	#==========================================================================================#
	# >>>>> ПРОВЕРКА ЧЁРНОГО СПИСКА И НЕЦЕНЗУРНОЙ ЛЕКСИКИ <<<<< #
	#==========================================================================================#

	if Functions.CheckBlacklist(Message.text, Bot, Cacher, User): return

	if ProfanityFilterObject.filter_text(Message.text):
		Functions.AnswerToObscene(Bot, User)
		return
	
	#==========================================================================================#
	# >>>>> ОБРАБОТКА REPLY-КНОПОК <<<<< #
	#==========================================================================================#

	CaseBuffer = Message.text[2:] if len(Message.text) > 2 else None

	match CaseBuffer:
		case "Поделиться с друзьям": Functions.SendShareMessage(Bot, Cacher, User)
		case "Переключить режим": Functions.SendModeSwitcher(Bot, User)

#==========================================================================================#
# >>>>> ОБРАБОТКА INLINE-КНОПОК <<<<< #
#==========================================================================================#

AdminPanel.decorators.inline_keyboards()

@Bot.callback_query_handler(func = lambda Callback: Callback.data == "after_subscribe")
def InlineButton(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Bot.answer_callback_query(Call.id)
	if not Functions.CheckSubscription(Master, Cacher, User, Settings["subscriptions"], autosend = False): return
	Master.safely_delete_messages(User.id, Call.message.id)

	Bot.send_animation(
		chat_id = User.id,
		animation = Cacher.get_real_cached_file("Data/Materials/Animation/after_subscribe.mp4", autoupload_type = types.InputMediaAnimation).file_id,
		caption = "<b><i>" + "- Ну все, удачки в пользовании!)" + "</i></b>",
		parse_mode = "HTML"
	)

@Bot.callback_query_handler(func = lambda Callback: Callback.data == "delete")
def InlineButton(Call: types.CallbackQuery):
	Master.safely_delete_messages(Call.from_user.id, Call.message.id)
	
@Bot.callback_query_handler(func = lambda Callback: Callback.data.startswith("switch_mode_"))
def InlineButton(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	User.set_property("mode", Call.data[12:])
	Master.safely_delete_messages(User.id, Call.message.id)

#==========================================================================================#
# >>>>> ОБРАБОТКА МЕДИА-ВЛОЖЕНИЙ <<<<< #
#==========================================================================================#

@Bot.message_handler(content_types = ["animation", "audio", "document", "photo", "video", "voice"])
def File(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	if AdminPanel.procedures.files(Bot, User, Message): return

	if Message.voice:

		try:
			FileInfo = Bot.get_file(Message.voice.file_id)
			FileURL = "https://api.telegram.org/file/bot" + Settings["bot_token"] + f"/{FileInfo.file_path}"
			UserTempDirectory = f"Data/Temp/{User.id}"
			if not os.path.exists(UserTempDirectory): os.makedirs(UserTempDirectory)
			VoicePath = f"Data/Temp/{User.id}/{FileInfo.file_id}.ogg"
			Functions.DownloadFile(FileURL, VoicePath)
			if SpeecherObject.ogg_to_wav(VoicePath): VoicePath = VoicePath[:-4] + ".wav"

			Bot.send_message(
				chat_id = User.id,
				text = SpeecherObject.recognize_speech(VoicePath) or "<i>Не удалось распознать текст.</i>",
				parse_mode = "HTML",
				reply_to_message_id = Message.id
			)
		except Exception as ExceptionData: print(ExceptionData)

		if os.path.exists(UserTempDirectory): shutil.rmtree(UserTempDirectory)

Bot.infinity_polling()