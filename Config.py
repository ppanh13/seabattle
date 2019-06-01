import json


def load():
	try:
		with open('config.json') as file:
			data = json.loads(file.read())
			return data
	except:
		print('Помилка при відкритті файла конфигурації! :(')