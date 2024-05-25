#!/usr/bin/python
# -*- coding: utf-8 -*-
import telebot
import logging
from telebot.types import BotCommand, BotCommandScope, Message
import time
import schedule
from threading import Thread
from keyboard import create_keyboard
from text import start_message, help_message, feedback_text
from validators import check_number_of_users, is_gpt_token_limit, is_stt_block_limit, is_tts_symbol_limit
from yandex_gpt import ask_gpt
from config import COUNT_LAST_MSG, ADMIN_IDS, LOGS, CATEGORIES, LEVELS, TIMER, ACCEPTABLE_VALUES, INGREDIENTS
from database import create_database, add_message, select_n_last_messages, menu
from speechkit import text_to_speech, speech_to_text
from creds import get_bot_token  # модуль для получения bot_token

bot = telebot.TeleBot(get_bot_token())  # создаём объект бота
settings = {}


# Команда /debug с доступом только для админов
@bot.message_handler(commands=["debug"])
def send_logs(message: Message):
    user_id = message.chat.id
    if user_id in ADMIN_IDS:
        try:
            with open(LOGS, "rb") as f:
                bot.send_document(message.chat.id, f)
                logging.info("логи отправлены")
        except telebot.apihelper.ApiTelegramException:
            bot.send_message(message.chat.id, "Логов пока нет.")
    else:
        bot.send_message(message.chat.id, "У Вас недостаточно прав для использования этой команды.")
        logging.info(f"{user_id} пытался получить доступ к логам, не являясь админом")


def register_comands(message: Message):
    commands = [  # Установка списка команд с областью видимости и описанием
        BotCommand("start", "запуск бота"),
        BotCommand("help", "основная информация о боте"),
        BotCommand("feedback", "оставить отзыв"),
        BotCommand("get_recipe", "выбрать рецепт"),
        BotCommand('set', 'Поставить таймер'),
        BotCommand('unset', 'Убрать таймер'),
        BotCommand('settings', 'Изменить/посмотреть настройки')]
    bot.set_my_commands(commands)
    BotCommandScope('private', chat_id=message.chat.id)


@bot.message_handler(commands=['settings'])
def send_settings(msg: Message):
    if not settings.get(msg.chat.id):
        settings[msg.chat.id] = {}
        settings[msg.chat.id]['Уровень'] = 'новичок'
        settings[msg.chat.id]['Приоритет ответа'] = 'любой'
    bot.send_message(msg.chat.id,
                     f'Ваши текущие настройки:\n '
                     f'{"\n".join(key + ' - ' + value for key, value in settings[msg.chat.id].items())}',
                     reply_markup=create_keyboard(['Поменять настройки']))
    bot.register_next_step_handler(msg, settings_handler)


def settings_handler(msg: Message):
    if msg.text == 'Поменять настройки':
        bot.send_message(msg.chat.id, f'Выбери пункт, который ты хочешь поменять:\n'
                                      f'{"\n".join(key for key, _ in settings[msg.chat.id].items())}',
                         reply_markup=create_keyboard([key for key, _ in settings[msg.chat.id].items()]))
        bot.register_next_step_handler(msg, handle_settings)
    else:
        handle_all(msg)


def handle_settings(msg: Message):
    if msg.text in settings[msg.chat.id].keys():
        bot.send_message(msg.chat.id, f'Выбери значение для параметра {msg.text}',
                         reply_markup=create_keyboard(ACCEPTABLE_VALUES[msg.text]))
        bot.register_next_step_handler(msg, set_settings, msg.text)


def set_settings(msg: Message, mode):
    if msg.text in ACCEPTABLE_VALUES[mode]:
        settings[msg.chat.id][mode] = msg.text
        bot.send_message(msg.chat.id, f'Параметр *{mode}* изменен на значение *{msg.text}*', parse_mode='markdown')
    else:
        bot.send_message(msg.chat.id, 'Выбери вариант из предложенных')


@bot.message_handler(commands=["feedback"])
def feedback_handler(message: Message):
    bot.send_message(message.chat.id, feedback_text.format(message.from_user,
                                                           bot.get_me()), parse_mode="markdown")
    bot.register_next_step_handler(message, feedback)


def feedback(message: Message):
    with open('creds/feedback.txt', 'a', encoding='utf-8') as f:
        f.write(f'{message.from_user.first_name}({message.from_user.id}) оставил отзыв - "{message.text}"\n')
        bot.send_message(message.chat.id, 'Спасибо за отзыв!')


# Команда /start
@bot.message_handler(commands=["start"])
def send_welcome(message: Message):
    if not settings.get(message.chat.id):
        settings[message.chat.id] = {}
        settings[message.chat.id]['Уровень'] = 'новичок'
        settings[message.chat.id]['Приоритет ответа'] = 'любой'
    logging.info("Отправка приветственного сообщения")
    bot.reply_to(message, start_message)
    register_comands(message)


@bot.message_handler(commands=['set'])
def set_timer_handler(msg: Message):
    if not schedule.get_jobs(msg.chat.id):
        bot.send_message(msg.chat.id, 'Чтобы поставить таймер, введи кол-во минут, на которые ты хотел бы'
                                      'поставить таймер',
                         reply_markup=create_keyboard(['5', '10', '15', '30']))
        bot.register_next_step_handler(msg, set_timer_thing, 0, 'minutes')
    else:
        hours = schedule.get_jobs(msg.chat.id)[0].next_run.hour
        minutes = schedule.get_jobs(msg.chat.id)[0].next_run.minute
        bot.send_message(msg.chat.id, f"У вас уже есть один таймер. Он прозвенит в"
                                      f" {hours}:{minutes}")


def set_timer_thing(msg: Message, minutes, mode):
    msgs = msg.text.split()
    for i in range(len(msgs)):
        if msgs[i].isdigit():
            thing = msgs[i]
            break
    else:
        thing = None
    if thing:
        thing = int(thing)
        if mode == 'hours':
            minutes += thing * 60
            schedule.every(minutes).minutes.do(alert, msg.chat.id).tag(msg.chat.id)
            bot.send_message(msg.chat.id, 'Таймер поставлен!')
        elif mode == 'minutes':
            minutes += thing
            bot.send_message(msg.chat.id, 'Теперь введи кол-во часов',
                             reply_markup=create_keyboard(['1', '2', '3', '4']))
            bot.register_next_step_handler(msg, set_timer_thing, minutes, 'hours')
    else:
        bot.send_message(msg.chat.id, 'Отправь число')


@bot.message_handler(commands=['unset'])
def unset_timer(msg: Message):
    if schedule.get_jobs(msg.chat.id):
        schedule.clear(msg.chat.id)
        bot.send_message(msg.chat.id, 'Таймер остановлен.')
    else:
        bot.send_message(msg.chat.id, 'У вас еще не поставлен таймер. Введите команду /set для того,'
                                      'чтобы его поставить.')


def alert(user_id):
    bot.send_message(user_id, "Таймер!")
    with open(TIMER, "rb") as t:
        bot.send_voice(user_id, t)
    schedule.clear(user_id)


@bot.message_handler(commands=['get_recipe'])
def recipe_handler_start(msg: Message):
    bot.send_message(msg.chat.id, 'Выбери категорию', reply_markup=create_keyboard(CATEGORIES))
    bot.register_next_step_handler(msg, recipe_handler_category)


def recipe_handler_category(msg: Message):
    if msg.text not in CATEGORIES:
        bot.send_message(msg.chat.id, 'Выбери вариант из предложенных')
        return
    bot.send_message(msg.chat.id, 'Теперь введи предпочтительные ингредиенты(не обязательно)\n'
                                  'Внизу есть варианты', reply_markup=create_keyboard(INGREDIENTS))
    bot.register_next_step_handler(msg, recipe_handler_indredients, msg.text)


def recipe_handler_indredients(msg: Message, cat):
    if msg.text != 'дальше':
        bot.send_message(msg.chat.id, menu(cat, msg.text), parse_mode='markdown')
    else:
        bot.send_message(msg.chat.id, menu(cat), parse_mode='markdown')


# команда /help
@bot.message_handler(commands=["help"])
def about_bot(message: Message):
    bot.send_message(message.chat.id, text=help_message)


def handle_text(message: Message, text):
    try:
        if settings.get(message.chat.id):
            user_id = message.from_user.id
            # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
            status_check_users, error_message = check_number_of_users(user_id)
            if not status_check_users:
                bot.send_message(user_id, error_message)  # мест нет =(
                return
            # БД: добавляем сообщение пользователя и его роль в базу данных
            full_user_message = [text, 'user', 0, 0, 0]
            add_message(user_id=user_id, full_message=full_user_message)
            # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
            # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
            last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
            # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
            total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
            if error_message:
                # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
                bot.send_message(user_id, error_message)
                return
            # GPT: отправляем запрос к GPT
            status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages, level=LEVELS.index(
                settings[message.chat.id]['Уровень'])+1)
            # GPT: обрабатываем ответ от GPT
            if not status_gpt:
                # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
                bot.send_message(user_id, answer_gpt)
                return
            # сумма всех потраченных токенов + токены в ответе GPT
            total_gpt_tokens += tokens_in_answer
            # БД: добавляем ответ GPT и потраченные токены в базу данных
            full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
            add_message(user_id=user_id, full_message=full_gpt_message)
            if settings[message.chat.id]['Приоритет ответа'] == 'аудио':
                status_tts, voice_response = text_to_speech(answer_gpt)
                if status_tts:
                    bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
                else:
                    bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
                return
            else:
                bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id, parse_mode="markdown")  # отвечаем
        else:
            send_welcome(message)
        # пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


def set_level(msg: Message):
    if not settings.get(msg.chat.id):
        settings[msg.chat.id] = {}
        settings[msg.chat.id]['Приоритет ответа'] = 'любой'
    settings[msg.chat.id]['Уровень'] = msg.text


@bot.message_handler(content_types=['voice', 'text'])
def handle_all(msg: Message):
    if not settings.get(msg.chat.id):
        bot.send_message(msg.chat.id, 'Введите, пожалуйста, ваш уровень знаний кулинарии в меню снизу',
                         reply_markup=create_keyboard(['Новичок', 'Знаток', "Профи", "Мастер", "Гений"]))
        bot.register_next_step_handler(msg, set_level)
    if msg.voice:
        bot.register_next_step_handler(msg, handle_voice, msg.voice)
    elif msg.text:
        bot.register_next_step_handler(msg, handle_text, msg.text)


def handle_voice(message: Message, voice):
    try:
        if settings.get(message.chat.id):
            user_id = message.from_user.id

            # Проверка на максимальное количество пользователей
            status_check_users, error_message = check_number_of_users(user_id)
            if not status_check_users:
                bot.send_message(user_id, error_message)
                return

            # Проверка на доступность аудиоблоков
            stt_blocks, error_message = is_stt_block_limit(user_id, voice.duration)
            if error_message:
                bot.send_message(user_id, error_message)
                return

            # Обработка голосового сообщения
            file_id = voice.file_id
            file_info = bot.get_file(file_id)
            file = bot.download_file(file_info.file_path)
            status_stt, stt_text = speech_to_text(file)
            if not status_stt:
                bot.send_message(user_id, stt_text)
                return

            # Запись в БД
            add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])

            # Проверка на доступность GPT-токенов
            last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
            total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
            if error_message:
                bot.send_message(user_id, error_message)
                return

            # Запрос к GPT и обработка ответа
            status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages, level=
                                                               LEVELS.index(settings[message.chat.id]['Уровень'])+1)
            if not status_gpt:
                bot.send_message(user_id, answer_gpt)
                return
            total_gpt_tokens += tokens_in_answer

            # Проверка на лимит символов для SpeechKit
            tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

            # Запись ответа GPT в БД
            add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])

            if error_message:
                bot.send_message(user_id, error_message)
                return
            if settings.get(message.chat.id):
                if settings[message.chat.id]['Приоритет ответа'] == 'текст':
                    bot.send_message(message.chat.id, answer_gpt)
                    return
                else:
                    # Преобразование ответа в аудио и отправка
                    status_tts, voice_response = text_to_speech(answer_gpt)
                    if status_tts:
                        bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
                    else:
                        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
        else:
            send_welcome(message)

    except Exception as e:
        logging.error(e)
        user_id = message.from_user.id
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение")


@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.from_user.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")


def _schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H",
        filename=LOGS,
        filemode="a",
        encoding='utf-8',
        force=True)
    create_database()  # Создание таблицы в БД
    Thread(target=_schedule, name='schedule', daemon=True).start()
    bot.infinity_polling()
