#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import logging
from config import LOGS, LANGUAGE, VOICE, URL_TTS, SPEECHKIT_MODEL, URL_STT
from creds import get_creds

IAM_TOKEN, FOLDER_ID = get_creds()  # получаем iam_token и folder_id из файлов

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.ERROR,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")


def text_to_speech(text):
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}"}
    data = {
        "text": text,
        "lang": LANGUAGE,
        "voice": VOICE,
        "folderId": FOLDER_ID}
    response = requests.post(URL_TTS, headers=headers, data=data)

    if response.status_code == 200:
        return True, response.content  # Возвращаем голосовое сообщение
    else:
        return False, logging.debug("При запросе в SpeechKit возникла ошибка")


def speech_to_text(data):
    # Указываем параметры запроса
    params = "&".join([
        f"topic={SPEECHKIT_MODEL}",
        f"folderId={FOLDER_ID}",
        f"lang={LANGUAGE}"
    ])
    # Аутентификация через IAM-токен
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}"}
    # Выполняем запрос
    response = requests.post(URL_STT + params, headers=headers, data=data)
    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
    else:
        return False, logging.debug("При запросе в SpeechKit возникла ошибка")
