import os
import time
import logging
from environs import Env
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram.utils.request import Request


# from ugc.models import (
#     Customers,
#     OrderStatuses,
#     Levels,
#     Forms,
#     Topping,
#     Berries,
#     Decors,
#     Orders,
# )

env = Env()
env.read_env()
TG_TOKEN = env.str("TG_TOKEN")

request = Request(connect_timeout=0.5, read_timeout=1.0)
bot = Bot(
    request=request,
    token=TG_TOKEN,
    base_url=getattr(settings, "PROXY_URL", None),
)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE, CHOICE = range(2)

storage_buttons = ['Крыло', 'Пирог', 'Комендант', 'Звезда']
choice_buttons = ['Сезонные вещи', 'Другое']


def chunks_generators(buttons, chunks_number):
    for button in range(0, len(buttons), chunks_number):
        yield buttons[button: button + chunks_number]


def keyboard_maker(buttons, number):
    keyboard = list(chunks_generators(buttons, number))
    markup = ReplyKeyboardMarkup(keyboard,
                                 resize_keyboard=True,
                                 one_time_keyboard=True)
    return markup


def start(update, context):
    user = update.message.from_user
    text = f'''
Привет, {user.first_name}!
Я помогу вам арендовать личную ячейку для хранения вещей. 
Давайте посмотрим адреса складов, чтобы выбрать ближайший!
'''
    storage_markup = keyboard_maker(storage_buttons, 3)
    photo_id = 'AgACAgQAAxkBAAIBMWGUIFP-VyC78fu_jw_Di7gPHcgUAALitzEbG4OgUE4AAaQx910LxQEAAwIAA20AAyIE'
    caption = 'Аренда ячеек в <b>Self Storage</b>'
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=photo_id, caption=caption, parse_mode='HTML')
    update.message.reply_text(text)
    time.sleep(1)
    second_text = '''
В Москве 4 склада:
<b>Крыло</b> - ул. Крыленко, 3Б ( м. Улица Дыбенко )
<b>Пирог</b> - Пироговская наб., 15 ( м. Площадь Ленина )
<b>Комендант</b> - пр.Сизова, 2А ( м. Комендантский проспект )
<b>Звезда</b> - Московское шоссе, 25 ( м. Звездная )   
'''
    update.message.reply_text(second_text, reply_markup=storage_markup,
                              parse_mode='HTML')
    return STORAGE


def storage(update, context):
    user_message = update.message.text
    context.user_data['storage'] = user_message
    choice_markup = keyboard_maker(choice_buttons, 2)
    update.message.reply_text('Что хотите хранить?', reply_markup=choice_markup)
    return CHOICE


def choice(update, context):
    user_message = update.message.text
    if user_message == 'Сезонные вещи':
        pass
    elif user_message == 'Другое':
        pass
    else:
        choice_markup = keyboard_maker(choice_buttons, 2)
        update.message.reply_text('Что хотите хранить?',
                                  reply_markup=choice_markup)


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f"Произошла ошибка: {e}"
            print(error_message)
            raise e

    return inner


@log_errors
def end(update, context):
    bot = context.bot
    bot.send_message(
        chat_id=update.callback_query.from_user.id, text="Всего Вам хорошего!"
    )
    return ConversationHandler.END


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):


        updater = Updater(bot=bot, use_context=True)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],

            states={

                STORAGE: [CommandHandler('start', start),
                       MessageHandler(Filters.text, storage)],

                CHOICE: [CommandHandler('start', start),
                        MessageHandler(Filters.text, choice)],

            },

            fallbacks=[CommandHandler("end", end)],
        )

        updater.dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
