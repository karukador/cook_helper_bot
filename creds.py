#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging
import time
from datetime import datetime
import requests
from config import LOGS, IAM_TOKEN_PATH, FOLDER_ID_PATH, BOT_TOKEN_PATH

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")


# получение нового iam_token
def create_new_token():
    url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {
        "Metadata-Flavor": "Google"
    }
    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()  # вытаскиваем из ответа iam_token
            # добавляем время истечения iam_token к текущему времени
            token_data['expires_at'] = time.time() + token_data['expires_in']
            # записываем iam_token в файл
            with open(IAM_TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Получен новый iam_token")
        else:
            logging.error(f"Ошибка получения iam_token. Статус-код: {response.status_code}")
    except Exception as e:
        logging.error(f"Ошибка получения iam_token: {e}")


# чтение iam_token и folder_id из файла
def get_creds():
    try:
        # чтение iam_token
        with open(IAM_TOKEN_PATH, 'r') as f:
            file_data = json.load(f)
            expiration = datetime.strptime(file_data["expires_at"][:26], "%Y-%m-%dT%H:%M:%S.%f")
        # если срок годности истёк
        if expiration < datetime.now():
            logging.info("Срок годности iam_token истёк")
            # получаем новый iam_token
            create_new_token()
    except:
        # если что-то пошло не так - получаем новый iam_token
        create_new_token()

    # чтение iam_token
    with open(IAM_TOKEN_PATH, 'r') as f:
        file_data = json.load(f)
        iam_token = file_data["access_token"]

    # чтение folder_id
    with open(FOLDER_ID_PATH, 'r') as f:
        folder_id = f.read().strip()

    return iam_token, folder_id


# чтение bot_token из файла
def get_bot_token():
    with open(BOT_TOKEN_PATH, 'r') as f:
        return f.read().strip()
