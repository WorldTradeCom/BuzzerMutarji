from dublib.CLI.TextStyler import Codes, GetStyledTextFromHTML, FastStyler, TextStyler
from dublib.Methods.Filesystem import ReadTextFile

from pathlib import Path
from os import PathLike
import os

class MaterialsValidator:
	"""Валидатор материалов."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def categories(self) -> tuple[str]:
		"""Последовательность категорий материалов."""

		return tuple(self.__Materials.keys())

	@property
	def materials(self) -> dict[str, tuple[str]]:
		"""Словарь материалов. Под ключами категорий находятся последовательности включаемых файлов."""

		return self.__Materials.copy()
	
	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	def __CheckFile(self, path: PathLike) -> bool:
		"""
		Проверяет существование файла и его заполненность контентом.

		:param path: Путь к файлу.
		:type path: PathLike
		:return: Состояние: валиден ли файл.
		:rtype: bool
		"""

		return all((self.__IsFileFilled(path), os.path.exists(path)))

	def __IsFileFilled(self, path: PathLike) -> bool | None:
		"""
		Проверяет, заполнен ли файл контентом.

		:param path: Путь к файлу.
		:type path: PathLike
		:return: Состояние: заполнен ли файл контентом. `None` в случае отсутствия файла.
		:rtype: bool | None
		"""

		if not os.path.exists(path): return
		File = Path(path)
		IsFileFilled = None

		if File.suffix in ("txt",):
			IsFileFilled = bool(ReadTextFile(path).strip())
		else:
			with open(path, "rb") as FileReader: IsFileFilled = bool(FileReader.read())

		return IsFileFilled

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Валидатор материалов."""

		self.__Materials: dict[str, dict[str, tuple]] = {
			"Animation": (
				"after_subscribe.mp4",
				"bad.mp4",
				"start.mp4",
				"subscribe.mp4"
			),
			"Photo": (
				"share.jpg",
			),
			"Text": (
				"blacklist_strings.txt",
			)
		}
		
	def is_files_exists(self, category: str, stdout: bool = True) -> bool:
		"""
		Проверяет наличие всех файлов указанной категории.

		:param category: Категория файлов.
		:type category: str
		:param stdout: Указывает, нужно ли выводить результаты проверки в консоль.
		:type stdout: bool
		:return: Состояние: найдены ли все файлы данной категории материалов.
		:rtype: bool
		"""

		Status = True

		for Filename in self.__Materials[category]:
			CurrentPath = f"Data/Materials/{category}/{Filename}"

			if not os.path.exists(CurrentPath):
				if Status and stdout: print(GetStyledTextFromHTML(f"In category <b>{category}</b> not found:"))
				Status = False
				if stdout: print(" > " + FastStyler(CurrentPath).colorize.red)

		if Status and stdout:
			Styler = TextStyler(text_color = Codes.Colors.Green)
			Text = GetStyledTextFromHTML(f"All files in category <b>{category}</b> exists.")
			print(Styler.get_styled_text(Text))

		return Status
	
	def is_files_filled(self, category: str, stdout: bool = True) -> bool:
		"""
		Проверяет наличие содержимого во всех файлах.

		:param category: Категория файлов.
		:type category: str
		:param stdout: Указывает, нужно ли выводить результаты проверки в консоль.
		:type stdout: bool
		:return: Состояние: имеют ли файлы содержимое.
		:rtype: bool
		"""

		Status = True

		for Filename in self.__Materials[category]:
			CurrentPath = f"Data/Materials/{category}/{Filename}"
			IsFileFilled = self.__IsFileFilled(CurrentPath)

			if not IsFileFilled:
				if Status and stdout: print(GetStyledTextFromHTML(f"In category <b>{category}</b> empty files:"))
				Status = False
				if stdout: print(" > " + FastStyler(CurrentPath).colorize.red)

		if Status and stdout:
			Styler = TextStyler(text_color = Codes.Colors.Green)
			Text = GetStyledTextFromHTML(f"All files in category <b>{category}</b> filled.")
			print(Styler.get_styled_text(Text))

		return Status

	def validate(self, stdout: bool = True) -> bool:
		"""
		Проводит валидацию всех категорий материалов.

		:param stdout: Указывает, нужно ли выводить результаты проверки в консоль.
		:type stdout: bool, optional
		:return: Состояние: успешна ли валидация.
		:rtype: bool
		"""

		Status = True

		if stdout: print("=== EXISTS ===")
		for Category in self.__Materials: Status = self.is_files_exists(Category, stdout)
		if stdout: print("=== FILLED ===")
		for Category in self.__Materials: Status = all((self.is_files_filled(Category, stdout), Status))

		return Status

	def print_materials(self):
		"""Выводит список требуемых материалов."""

		for Category in self.__Materials:
			print("=== " + Category.upper() + " ===")

			for Filename in self.__Materials[Category]:
				CurrentPath = f"Data/Materials/{Category}/{Filename}"
				print(" > ", end = "")
				if self.__CheckFile(CurrentPath): print(FastStyler(CurrentPath).colorize.green)
				else: print(FastStyler(CurrentPath).colorize.red)