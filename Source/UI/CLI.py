from dublib.CLI.Terminalyzer import Command

COMMANDS: list[Command] = list()

Com = Command("materials", "Выводит список материалов.")
COMMANDS.append(Com)

Com = Command("translate", "Переводит текст.")
ComPos = Com.create_position("TEXT", "Текст для перевода.", important = True)
ComPos.add_argument()
ComPos = Com.create_position("MODE", "Режим перевода.", important = True)
ComPos.add_flag("from", "С зумерского на нормальный.")
ComPos.add_flag("to", "С нормального на зумерский.")
Com.base.add_flag("json", "Prints result as JSON string.")
COMMANDS.append(Com)

Com = Command("validate", "Проводит проверку наличия материалов.")
COMMANDS.append(Com)