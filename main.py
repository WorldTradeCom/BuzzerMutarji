from Source.UI.Keyboards import InlineKeyboards, ReplyKeyboards
from Source.Core.Translator import TranslationModes, Translator
from Source.Core.Materials import MaterialsValidator
from Source.TeleBotAdminPanel import Panel, Modules
from Source.UI.DebugSender import DebugSender
from Source.Core.Speecher import Speecher
from Source.UI.CLI import COMMANDS
from Source import Functions

from dublib.TelebotUtils import TeleCache, TeleMaster, UsersManager
from dublib.Methods.System import CheckPythonMinimalVersion, Clear
from dublib.Methods.Filesystem import MakeRootDirectories
from dublib.CLI.Terminalyzer import Terminalyzer
from dublib.Engine.Configurator import Config
from dublib.Methods.Data import Zerotify

import shutil
import os

from apscheduler.schedulers.background import BackgroundScheduler
from badwords import ProfanityFilter
from telebot import types
import telebot
import orjson

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

Directories = (
	"Data/Materials",
	"Data/Materials/Animation",
	"Data/Materials/Photo",
	"Data/Materials/Text",
)

CheckPythonMinimalVersion(3, 10)
MakeRootDirectories(Directories)

Settings = Config("Settings.json")
Settings.load()

TranslatorObject = Translator()
NeuroHubOptions: dict = Settings["neurohub"]
TranslatorObject.set_neurohub_options(
	port = NeuroHubOptions["port"],
	source = NeuroHubOptions["source"],
	model = NeuroHubOptions["model"],
	force_proxy = NeuroHubOptions["force_proxy"]
)

#==========================================================================================#
# >>>>> ОБРАБОТКА АРГУМЕНТОВ ЗАПУСКА <<<<< #
#==========================================================================================#

Analyzer = Terminalyzer()
Analyzer.helper.enable(True)
CommandData = Analyzer.check_commands(COMMANDS)

if CommandData and CommandData.name:
	Cased = True

	match CommandData.name:

		case "help": pass

		case "materials": 
			Clear()
			MaterialsValidator().print_materials()

		case "validate":
			Clear()
			MaterialsValidator().validate()

		case "translate":
			Mode = TranslationModes.From if CommandData.check_key("from") else TranslationModes.To
			Result = TranslatorObject.translate(Mode, CommandData.arguments[0], CommandData.get_key_value("additional"))
			Result = {
				"code": Result.code,
				"text": Result.value,
				"messages": Result.messages
			}
			
			if CommandData.check_flag("json"): print(orjson.dumps(Result).decode("utf-8"))
			else: print(Result["text"])

		case _: Cased = False

	if Cased: exit(0)

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ОБЪЕКТОВ <<<<< #
#==========================================================================================#

Clear()
Bot = telebot.TeleBot(Settings["bot_token"])
Master = TeleMaster(Bot)
UsersManagerObject = UsersManager("Data/Users")
UsersManagerObject.remove_flags("in-generation")
Cacher = TeleCache()
Cacher.set_bot(Bot)
Cacher.set_chat_id(Settings["cache_chat_id"])
ProfanityFilterObject = ProfanityFilter()
ProfanityFilterObject.init(["ru", "en"])
AdminPanel = Panel(Bot, UsersManagerObject, Settings["password"])
SpeecherObject = Speecher(Settings["vosk_model"])
Scheduler = BackgroundScheduler()
Scheduler.add_job(UsersManagerObject.set_property, args = ("daily_points", 3), trigger = "cron", hour = "0", minute = "0")
Scheduler.start()

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ПАНЕЛИ УПРАВЛЕНИЯ <<<<< #
#==========================================================================================#

AdminPanel = Panel(Bot, UsersManagerObject, Settings["password"])

TBAP_TREE = {
	"📊 Статистика": Modules.SM_Statistics,
	"✉️ Рассылка": Modules.SM_Mailing,
	"❌ Закрыть": Modules.SM_Close
}

AdminPanel.set_tree(TBAP_TREE)

#==========================================================================================#
# >>>>> ОБРАБОТКА КОМАНД <<<<< #
#==========================================================================================#

@Bot.message_handler(commands = ["admin"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	Password = Message.text.split(" ")[1:]
	Password = " ".join(Password).strip()

	if not AdminPanel.login(User, Zerotify(Password)):
		Bot.send_message(User.id, "Доступ запрещён.")

	else:
		Keyboard = AdminPanel.open(User)
		Bot.send_message(User.id, "Панель управления открыта.", reply_markup = Keyboard)

@Bot.message_handler(commands = ["debug"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	DebugSender(Bot, User).send()

@Bot.message_handler(commands = ["start"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	if not User.has_property("invited_by"): Functions.ProcessReferalLink(Bot, UsersManagerObject, User, Message.text)

	User.suppress_saving(True)
	User.set_property("mode", "to", force = False)
	User.set_property("daily_points", 3, force = False)
	User.set_property("bonus_points", 0, force = False)
	User.set_property("invited_by", None, force = False)
	User.set_property("invited_users", list(), force = False)
	User.suppress_saving(False)

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
	if AdminPanel.procedures.text(Message): return
	if not Functions.CheckSubscription(Master, Cacher, User, Settings["subscriptions"]): return

	#---> Проверка чёрного списка и нецензурной лексики.
	#==========================================================================================#
	if Functions.CheckBlacklist(Message.text, Bot, Cacher, User): return

	if ProfanityFilterObject.filter_text(Message.text):
		Functions.AnswerToObscene(Bot, User)
		return
	
	#---> Обработка Reply-кнопок.
	#==========================================================================================#
	CaseBuffer = Message.text[2:] if len(Message.text) > 2 else None

	match CaseBuffer:
		case "Поделиться с друзьям": Functions.SendShareMessage(Bot, Cacher, User)
		case "Переключить режим": Functions.SendModeSwitcher(Bot, User)

		#---> Перевод.
		#==========================================================================================#
		case _:
			if Functions.CheckPointsLimit(Bot, User): return
			if Functions.CheckMessageLength(Bot, User, Message.text): return
			Bot.send_chat_action(User.id, "typing")
			Functions.TranslateText(Bot, User, TranslatorObject, Message.text)
			if User.check_flags("invation_unnotificated"): Functions.SendReferralNotification(Bot, UsersManagerObject, User)

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

@Bot.callback_query_handler(func = lambda Callback: Callback.data == "translate")
def InlineButton(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Bot.answer_callback_query(Call.id)
	Bot.send_chat_action(User.id, "typing")
	Functions.TranslateText(Bot, User, TranslatorObject, Call.message.text)

#==========================================================================================#
# >>>>> ОБРАБОТКА МЕДИА-ВЛОЖЕНИЙ <<<<< #
#==========================================================================================#

@Bot.message_handler(content_types = ["animation", "audio", "document", "photo", "video", "voice"])
def File(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

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
				reply_to_message_id = Message.id,
				reply_markup = InlineKeyboards.Translate()
			)
		except Exception as ExceptionData: print(ExceptionData)

		if os.path.exists(UserTempDirectory): shutil.rmtree(UserTempDirectory)

Bot.infinity_polling()