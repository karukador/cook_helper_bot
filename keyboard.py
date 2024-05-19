from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def create_keyboard(texts):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for text in texts:
        markup.add(KeyboardButton(text))
    return markup
