#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
import math
from config import LOGS, MAX_USERS, MAX_USER_GPT_TOKENS, MAX_USER_STT_BLOCKS, MAX_USER_TTS_SYMBOLS
from database import count_users, count_all_limits
from yandex_gpt import count_gpt_tokens

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.ERROR,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")


# получаем количество уникальных пользователей, кроме самого пользователя
def check_number_of_users(user_id):
    count = count_users(user_id)
    if count is None:
        return None, "Ошибка при работе с БД"
    if count > MAX_USERS:
        return None, "Превышено максимальное количество пользователей"
    return True, ""


# проверяем, не превысил ли пользователь лимиты на общение с GPT
def is_gpt_token_limit(messages, total_spent_tokens):
    all_tokens = count_gpt_tokens(messages) + total_spent_tokens
    if all_tokens > MAX_USER_GPT_TOKENS:
        return None, f"Превышен общий лимит GPT-токенов {MAX_USER_GPT_TOKENS}"
    return all_tokens, ""


# проверяем не превысил ли пользователь лимиты на преобразование аудио в текст
def is_stt_block_limit(user_id: int, duration: int) -> (int | None, str):
    audio_blocks = math.ceil(duration / 15)  # переводим секунды в аудиоблоки и округляем в большую сторону
    # функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = count_all_limits(user_id, 'stt_blocks') + audio_blocks

    # проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        return None, "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"

    # сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks > MAX_USER_STT_BLOCKS:
        return None, f"Превышен общий лимит SpeechKit STT {MAX_USER_STT_BLOCKS}"

    # если всё ок - возвращаем размер этого голосового сообщения
    return audio_blocks, ""


# проверяем не превысил ли пользователь лимиты на преобразование текста в аудио
def is_tts_symbol_limit(user_id: int, text: str) -> (int | None, str):
    text_symbols = len(text)  # считаем количество символов в тексте
    # функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_limits(user_id, 'tts_symbols') + text_symbols

    # сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols > MAX_USER_TTS_SYMBOLS:
        return None, f"Превышен общий лимит SpeechKit TTS {MAX_USER_TTS_SYMBOLS}"

    # если всё ок - возвращаем кол-во символов в сообщении
    return text_symbols, ""
