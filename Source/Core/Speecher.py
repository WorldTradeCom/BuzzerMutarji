from Source.Functions import DownloadFile

from dublib.CLI.TextStyler import FastStyler
from dublib.Methods.Data import Zerotify

from os import PathLike
import zipfile
import shutil
import wave
import os

from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import orjson

class Speecher:
	"""Преобразователь голоса в речь."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckModel(self, model: str) -> bool:
		"""
		Проверяет, установлена ли модель **VOSK**.

		:param model: Название модели из [списка](https://alphacephei.com/vosk/models) **VOSK**.
		:type model: str
		:return: Возвращает `True`, если модель установлена.
		:rtype: bool
		"""

		return os.path.exists(f"Data/VOSK/{model}")

	def __InstallModel(self, model: str):
		"""
		Устанавливает выбранную модель **VOSK**.

		:param model: Название модели из [списка](https://alphacephei.com/vosk/models) **VOSK**.
		:type model: str
		"""

		try:
			ModelDirectoryPath = f"Data/VOSK/{model}"
			if os.path.exists(ModelDirectoryPath): shutil.rmtree(ModelDirectoryPath)
			
			ModelArchivePath = f"Data/{model}.zip"
			DownloadFile(f"https://alphacephei.com/vosk/models/{model}.zip", ModelArchivePath)
			with zipfile.ZipFile(ModelArchivePath, "r") as ZipReader: ZipReader.extractall("Data/VOSK")
			os.remove(ModelArchivePath)

		except: print(FastStyler(f"Unable install \"{model}\" VOSK model.").colorize.red)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, model: str):
		"""
		Преобразователь голоса в речь.

		:param model: Название каталога с используемой моделью **VOSK**.
		:type model: PathLike
		"""

		if not self.__CheckModel(model): self.__InstallModel(model)
		self.__Model = Model(f"Data/VOSK/{model}")

	def ogg_to_wav(self, path: PathLike) -> bool:
		"""
		Преобразует файл *.ogg в *.wav формат. В случае успеха перезаписывает исходный файл.

		:param path: Путь к исходному файлу.
		:type path: PathLike
		:return: Возвращает `True`, если преобразование успешно.
		:rtype: bool
		"""

		try:
			Audio = AudioSegment.from_file(path, format = "ogg")
			Audio = Audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
			Audio.export(path[:-4] + ".wav", format = "wav")
			os.remove(path)

		except Exception as ExceptionData:
			print(ExceptionData)
			return False

		return True
	
	def recognize_speech(self, path: PathLike) -> str | None:
		"""
		Распознаёт речь в аудиофайле.

		:param path: Путь к *.wav файлу.
		:type path: PathLike
		:return: Распознанный текст или `None` в случае ошибки или отсутствия таковой.
		:rtype: str | None
		"""

		Text = str()
		
		with wave.open(path, "rb") as WaveReader:
			Recognizer = KaldiRecognizer(self.__Model, WaveReader.getframerate())

			while True:
				Data = WaveReader.readframes(4000)
				if len(Data) == 0: break

				if Recognizer.AcceptWaveform(Data):
					Result: dict = orjson.loads(Recognizer.Result())
					Text += Result.get("text", "") + " "

		return Zerotify(Text)