#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import List, Dict

MAX_USERS = 3  # максимальное кол-во пользователей
MAX_GPT_TOKENS = 120  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 4  # кол-во последних сообщений из диалога

# лимиты для пользователя
MAX_USER_STT_BLOCKS = 10  # 10 аудиоблоков
MAX_USER_TTS_SYMBOLS = 5_000  # 5 000 символов
MAX_USER_GPT_TOKENS = 2_000  # 2 000 токенов

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
GPT_MODEL = "yandexgpt-lite"
SYSTEM_PROMPT: list[dict[str, str]] = [{"role": "system", "text":
                                            "Ты помощник на кухне. Не объясняй пользователю, что ты умеешь и можешь. "
                                            "Чётко и понятно"
                                            "отвечай на вопросы пользователя. Не используй диалоги. Не трать символы "
                                            "просто так, используй их с умом. "
                                            "Твоя главная задача: облегчить быт пользователя."
                                            "Уровень знаний пользователя: {} из 5, где 1 - абсолютный новичок,"
                                            "а 5 - опытный шеф-повар."
                                            "Старайся отвечать на вопросы, основываясь на уровне знаний пользователя."}]
ADMIN_IDS: list = [1234, 4321]
LEVELS = ['Новичок', 'Знаток', "Профи", "Мастер", "Гений"]
URL_TOKEN = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"

# speechkit
URL_TTS = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
URL_STT = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?"
LANGUAGE = "ru-RU"
SPEECHKIT_MODEL = "general"  # используем основную версию модели
VOICE = "filipp"  # желаемый голос можно выбрать в списке - https://yandex.cloud/ru/docs/speechkit/tts/voices

# utils
HOME_DIR = '.'  # путь к папке с проектом
LOGS = f'{HOME_DIR}/logs.log'  # файл для логов
DB_FILE = f'{HOME_DIR}/database.db'  # файл для базы данных

IAM_TOKEN_PATH = f'{HOME_DIR}/creds/iam_token.txt'  # файл для хранения iam_token
FOLDER_ID_PATH = f'{HOME_DIR}/creds/folder_id.txt'  # файл для хранения folder_id
BOT_TOKEN_PATH = f'{HOME_DIR}/creds/bot_token.txt'  # файл для хранения bot_token
DB_RECIPES = f'{HOME_DIR}/recipes.sqlite'
CATEGORIES = ["основные", "завтраки", "салаты", "пицца-паста"]
