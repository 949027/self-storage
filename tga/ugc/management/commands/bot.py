import os
import time
import logging
from environs import Env
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram.utils.request import Request


from ugc.models import Warehouses, SeasonalItems

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAREHOISES, CHOICE, ANOTHER, PERIOD, ORDER, SEASON, AMOUNT = range(7)

choice_buttons = ["Сезонные вещи", "Другое"]


def chunks_generators(buttons, chunks_number):
    for button in range(0, len(buttons), chunks_number):
        yield buttons[button : button + chunks_number]


def keyboard_maker(buttons, number):
    keyboard = list(chunks_generators(buttons, number))
    markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    return markup


def start(update, context):
    user = update.message.from_user
    text = f"""Привет, {user.first_name}!
           Я помогу вам арендовать личную ячейку для хранения вещей.
           Давайте посмотрим адреса складов, чтобы выбрать ближайший!"""
    caption = "Аренда ячеек в <b>Self Storage</b>"
    bot.send_photo(
        chat_id=update.message.chat_id,
        photo='https://pilot196.ru/upload/iblock/c9f/tovar_sklad_2.jpg',
        caption=caption,
        parse_mode="HTML",
    )
    update.message.reply_text(text)
    time.sleep(1)
    warehouses = Warehouses.objects.all()
    warehouse_buttons = []
    for warehouse in warehouses:
        warehouse_buttons.append(warehouse.name)
    warehouse_markup = keyboard_maker(warehouse_buttons, 2)
    menu_text = f"""В Москве 4 склада:
                  <b>Крыло</b> - ул. Крыленко, 3Б ( м. Улица Дыбенко )
                  <b>Пирог</b> - Пироговская наб., 15 ( м. Площадь Ленина )
                  <b>Комендант</b> - пр.Сизова, 2А ( м. Комендантский проспект )
                  <b>Звезда</b> - Московское шоссе, 25 ( м. Звездная )"""
    context.user_data["menu_text"] = menu_text
    context.user_data["warehouse_markup"] = warehouse_markup
    update.message.reply_text(
        menu_text, reply_markup=warehouse_markup, parse_mode="HTML"
    )
    return WAREHOISES


def warehouses(update, context):
    user_message = update.message.text
    context.user_data["warehouse"] = user_message
    choice_markup = keyboard_maker(choice_buttons, 2)
    update.message.reply_text(
        "Что хотите хранить?", reply_markup=choice_markup
    )
    return CHOICE


def choice(update, context):
    user_message = update.message.text
    if user_message == "Сезонные вещи":
        things = SeasonalItems.objects.all()
        things_buttons = []
        for thing in things:
            things_buttons.append(thing.item_name)
        things_markup = keyboard_maker(things_buttons, 2)
        update.message.reply_text("Выберете вещи.",
                                  reply_markup=things_markup)
        return SEASON
    elif user_message == "Другое":
        another_buttons = list(range(1, 11))
        another_markup = keyboard_maker(another_buttons, 5)
        update.message.reply_text("Выберите габариты ячейки")
        update.message.reply_text(
            "599 руб - первый 1 кв.м., далее +150 руб за каждый кв. метр в месяц"
        )
        update.message.reply_text("Сколько кв. метров вам нужно?",
                                  reply_markup=another_markup)
        return ANOTHER
    else:
        choice_markup = keyboard_maker(choice_buttons, 2)
        update.message.reply_text(
            "Что хотите хранить?", reply_markup=choice_markup
        )


def season(update, context):
    user_message = update.message.text
    context.user_data["seasonal_item"] = user_message
    amount_buttons = list(range(1, 6))
    amount_markup = keyboard_maker(amount_buttons, 5)
    update.message.reply_text(
        "Выберите или введите кол-во.", reply_markup=amount_markup)
    return AMOUNT


def amount(update, context):
    user_message = update.message.text
    context.user_data["amount"] = user_message
    amount_buttons = list(range(1, 6))
    amount_markup = keyboard_maker(amount_buttons, 5)
    update.message.reply_text(
        "Ещё не готово.", reply_markup=amount_markup)


def another(update, context):
    user_message = update.message.text
    context.user_data["square_meters"] = user_message
    another_buttons = list(range(1, 13))
    another_markup = keyboard_maker(another_buttons, 4)
    text = "Мы можем хранить можем сдать ячейку до 12 месяцев"
    update.message.reply_text(text)
    update.message.reply_text("Сколько месяцев вам нужно?",
                              reply_markup=another_markup)
    return PERIOD


def period(update, context):
    user_message = update.message.text
    context.user_data["period"] = user_message
    period_buttons = ["Забронировать", "Назад"]
    period_markup = keyboard_maker(period_buttons, 1)
    square_meters = context.user_data.get("square_meters")
    warehouse = context.user_data.get("warehouse")
    text = f"""
Ваш заказ:
Склад: {warehouse}
Ячейка: {square_meters} кв. м
Период: {user_message} месяц(ев)
Цена: пока считаем)
"""
    update.message.reply_text(text, reply_markup=period_markup)
    return ORDER


def order(update, context):
    user_message = update.message.text
    if user_message == "Забронировать":
        update.message.reply_text("Ещё не готово")
    elif user_message == "Назад":
        warehouse_markup = context.user_data.get("warehouse_markup")
        menu_text = context.user_data.get("menu_text")
        update.message.reply_text(
            menu_text, reply_markup=warehouse_markup, parse_mode="HTML"
        )
        return WAREHOISES
    else:
        pass


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f"Произошла ошибка: {e}"
            print(error_message)
            raise e

    return inner


# @log_errors
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
                WAREHOISES: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, warehouses),
                ],
                CHOICE: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, choice),
                ],
                ANOTHER: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, another),
                ],
                PERIOD: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, period),
                ],
                ORDER: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, order),
                ],
                SEASON: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, season),
                ],
                AMOUNT: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, amount),
                ],
            },
            fallbacks=[CommandHandler("end", end)],
        )

        updater.dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
