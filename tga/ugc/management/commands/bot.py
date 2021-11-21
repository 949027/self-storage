import qrcode
import json
import requests
import re
import os
import time
import logging
from environs import Env

import phonenumbers
import random

# import qrcode

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.conf import settings

# from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telegram import Bot
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    Filters,
)
from telegram.utils.request import Request

from ugc.models import (
    Warehouses,
    SeasonalItems,
    Customers,
    SeasonalItemsPrice,
    AnotherItemsPrice,
    Orders,
)

from ugc.management.commands.price import (
    get_meter_price,
    get_think_price,
    get_think_button_prices,
    get_another_button_prices,
)

from ugc.management.commands.location import get_distance_buttons

env = Env()
env.read_env()
TG_TOKEN = env.str("TG_TOKEN")
ukassa_token = env.str("UKASSA_TOKEN")

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

(
    WAREHOISES,
    CHOICE,
    ANOTHER,
    PERIOD,
    ORDER,
    SEASON,
    AMOUNT,
    CHOICE_PERIOD,
    CHECK_USER,
    USER_LAST_NAME,
    USER_PHONE_NUMBER,
    USER_PASSPORT_ID,
    USER_BIRTHDAY,
    SAVE_USER,
    MAKE_PAYMENT,
    CATCH_PAYMENT,
    CREATE_QR,
    USER_FIRST_NAME,
    GET_LOCATION,
) = range(19)

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


def save_customer(context):
    customer = Customers(
        telegram_id=context.user_data["telegram_id"],
        phone_number=context.user_data["phone_number"],
        first_name=context.user_data["first_name"],
        last_name=context.user_data["last_name"],
        passport_id=context.user_data["passport_id"],
        birthday=context.user_data["birthday"],
    )
    customer.save()

    return customer


def save_order(context):
    warehouse_name = context.user_data["warehouse"]
    warehouse = Warehouses.objects.get(name=warehouse_name)
    seasonal_item = None
    if context.user_data["seasonal_item"]:
        seasonal_item = SeasonalItems.objects.get(
            item_name=context.user_data["seasonal_item"]
        )
    today = date.today()
    if context.user_data["period_extension"] == "мес.":
        end_date = today + relativedelta(months=context.user_data["period"])
    elif context.user_data["period_extension"] == "нед.":
        end_date = today + relativedelta(weeks=context.user_data["period"])
    square_meters = None
    if "square_meters" in context.user_data:
        square_meters = context.user_data["square_meters"]

    order = Orders(
        customer=context.user_data["customer"],
        warehouse=warehouse,
        seasonal_item=seasonal_item,
        thing_type=context.user_data["choice"],
        cell_size=square_meters,
        amount=context.user_data["amount"] or None,
        comment="" or None,
        start_date=today,
        end_date=today,
        cost=context.user_data["price"] or 0,
    )
    order.save()


def start(update, context):
    user = update.message.from_user
    text = f"""Привет, {user.first_name}!
           Я помогу вам арендовать личную ячейку для хранения вещей.
           Давайте посмотрим адреса складов, чтобы выбрать ближайший!"""
    caption = "Аренда ячеек в <b>Self Storage</b>"
    bot.send_photo(
        chat_id=update.message.chat_id,
        photo="https://pilot196.ru/upload/iblock/c9f/tovar_sklad_2.jpg",
        caption=caption,
        parse_mode="HTML",
    )
    update.message.reply_text(text)
    warehouses = Warehouses.objects.all()
    warehouse_buttons = []
    menu_text = ""
    for warehouse in warehouses:
        warehouse_buttons.append(warehouse.name)
        warehouse_card = Warehouses.objects.get(name=warehouse.name)
        menu_text += f"<b>{warehouse.name}</b> - {warehouse_card.address}\n"
    location_button = KeyboardButton(
        "Отправить геопозицию", request_location=True
    )
    warehouse_buttons.append(location_button)
    warehouse_markup = keyboard_maker(warehouse_buttons, 2)
    context.user_data["menu_text"] = menu_text
    context.user_data["warehouse_markup"] = warehouse_markup
    update.message.reply_text(
        menu_text, reply_markup=warehouse_markup, parse_mode="HTML"
    )
    return WAREHOISES


def get_location(bot, update):
    distance_buttons = get_distance_buttons(bot.message.location)
    distance_markup = keyboard_maker(distance_buttons, 2)
    bot.message.reply_text("мы получили ваше местоположение!")
    bot.message.reply_text("Выберите склад", reply_markup=distance_markup)


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
    context.user_data["choice"] = user_message
    if user_message == "Сезонные вещи":
        things = SeasonalItems.objects.all()
        things_buttons = []
        for thing in things:
            things_buttons.append(thing.item_name)
        context.user_data["things_buttons"] = things_buttons
        things_markup = keyboard_maker(things_buttons, 2)
        update.message.reply_text(
            """
        Стоимость хранения:
        1 лыжи - 100 р/неделя или 300 р/мес
        1 сноуборд - 100 р/неделя или 300 р/мес
        1 велосипед - 150 р/ неделя или 400 р/мес
        4 колеса - 200 р/мес"""
        )
        update.message.reply_text("Выберете вещи.", reply_markup=things_markup)
        return SEASON
    elif user_message == "Другое":
        another_buttons = list(range(1, 11))
        another_markup = keyboard_maker(another_buttons, 5)
        update.message.reply_text("Выберите габариты ячейки")
        update.message.reply_text(
            "599 руб - первый 1 кв.м., далее +150 руб за каждый кв. метр в месяц"
        )
        update.message.reply_text(
            "Сколько кв. метров вам нужно?", reply_markup=another_markup
        )
        return ANOTHER
    else:
        choice_markup = keyboard_maker(choice_buttons, 2)
        update.message.reply_text(
            "Что хотите хранить?", reply_markup=choice_markup
        )


def season(update, context):
    user_message = update.message.text
    context.user_data["seasonal_item"] = user_message
    amount_buttons = list(map(str, list(range(1, 6))))
    amount_markup = keyboard_maker(amount_buttons, 5)
    update.message.reply_text(
        "Выберите или введите кол-во.", reply_markup=amount_markup
    )
    return AMOUNT


def amount(update, context):
    user_message = update.message.text
    context.user_data["amount"] = user_message
    things = context.user_data.get("things_buttons")
    thing = context.user_data.get("seasonal_item")
    context.user_data["amount"] = user_message
    if thing in things[:-1]:
        period_buttons = ["Недели", "Месяцы"]
        period_markup = keyboard_maker(period_buttons, 5)
        update.message.reply_text("Максимальный срок хранения 6 месяцев.")
        update.message.reply_text(
            "Выберите срок хранения, недели или месяцы.",
            reply_markup=period_markup,
        )
        return CHOICE_PERIOD
    elif thing == "колеса":
        context.user_data["period_extension"] = "мес."
        seasonal_item = context.user_data.get("seasonal_item")
        amount = context.user_data.get("amount")
        period_buttons = get_think_button_prices(
            seasonal_item, "мес.", 6, amount
        )
        period_markup = keyboard_maker(period_buttons, 3)
        update.message.reply_text("Максимальный срок хранения 6 месяцев.")
        update.message.reply_text(
            "Укажите сколько месяцев вам нужно.", reply_markup=period_markup
        )
        return PERIOD


def choice_period(update, context):
    user_message = update.message.text
    seasonal_item = context.user_data.get("seasonal_item")
    amount = context.user_data.get("amount")
    if user_message == "Недели":
        context.user_data["period_extension"] = "нед."
        period_buttons = get_think_button_prices(
            seasonal_item, "нед.", 3, amount
        )
        period_markup = keyboard_maker(period_buttons, 1)
        update.message.reply_text(
            "Укажите сколько недель вам нужно.", reply_markup=period_markup
        )
        return PERIOD
    elif user_message == "Месяцы":
        context.user_data["period_extension"] = "мес."
        period_buttons = get_think_button_prices(
            seasonal_item, "мес.", 6, amount
        )
        period_markup = keyboard_maker(period_buttons, 3)
        update.message.reply_text(
            "Укажите сколько месяцев вам нужно.", reply_markup=period_markup
        )
        return PERIOD


def another(update, context):
    user_message = update.message.text
    context.user_data["square_meters"] = user_message
    context.user_data["period_extension"] = "мес."
    another_buttons = get_another_button_prices(
        12, user_message
    )  # list(map(str, list(range(1, 13))))
    another_markup = keyboard_maker(another_buttons, 3)
    text = "Мы можем хранить можем сдать ячейку до 12 месяцев"
    update.message.reply_text(text)
    update.message.reply_text(
        "Сколько месяцев вам нужно?", reply_markup=another_markup
    )
    return PERIOD


def get_period(update, context):
    user_message = update.message.text
    period = int(user_message.split()[0])
    context.user_data["period"] = period
    period_buttons = ["Забронировать", "Назад"]
    period_markup = keyboard_maker(period_buttons, 1)
    choice = context.user_data.get("choice")
    warehouse = context.user_data.get("warehouse")
    if choice == "Другое":
        square_meters = context.user_data.get("square_meters")
        period_extension = context.user_data.get("period_extension")
        price = get_meter_price(period, square_meters)
        text = f"""Ваш заказ:
               Склад: {warehouse}
               Ячейка: {square_meters} кв. м
               Период: {period} {period_extension}
               Цена: {int(price)} p."""
    elif choice == "Сезонные вещи":
        seasonal_item = context.user_data.get("seasonal_item")
        period_extension = context.user_data.get("period_extension")
        amount = context.user_data.get("amount")
        price = get_think_price(
            seasonal_item, period_extension, period, amount
        )
        text = f"""Ваш заказ:
                Склад: {warehouse}
                Вещь: {seasonal_item}
                Количество: {amount} шт.
                Период: {period} {period_extension}
                Цена: {int(price)} p."""
    update.message.reply_text(text, reply_markup=period_markup)
    context.user_data["price"] = price
    return ORDER


def order(update, context):
    user_message = update.message.text
    if user_message == "Забронировать":
        reg_buttons = ["Далее"]
        reg_markup = keyboard_maker(reg_buttons, 1)
        update.message.reply_text(
            "Приступим к регистрации!", reply_markup=reg_markup
        )
        return CHECK_USER
    elif user_message == "Назад":
        warehouse_markup = context.user_data.get("warehouse_markup")
        menu_text = context.user_data.get("menu_text")
        update.message.reply_text(
            menu_text, reply_markup=warehouse_markup, parse_mode="HTML"
        )
        return WAREHOISES


def check_register_user(update, context):
    global _telegram_id
    global _user_last_name

    _telegram_id = update.message.chat_id
    context.user_data["telegram_id"] = _telegram_id

    customer = Customers.objects.filter(telegram_id=_telegram_id)
    if customer.count() == 0:
        pdn_file_name = "pdn.pdf"
        pdn_file_path = os.path.join(os.getcwd(), pdn_file_name)

        bot = context.bot
        bot.send_document(update.message.chat.id, open(pdn_file_path, "rb"))

        agreement_buttons = ["Согласен", "Не согласен"]
        agreement_markup = keyboard_maker(agreement_buttons, 2)

        update.message.reply_text(
            "Для продолжения работы Вам необходимо принять согласие"
            + "на обработку персональных данных",
            reply_markup=agreement_markup,
        )
        return USER_FIRST_NAME
    else:
        bot = context.bot
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Вы уже зарегистрированы в системе:",
        )
        context.user_data["customer"] = customer[0]
        reg_buttons = ["Далее"]
        reg_markup = keyboard_maker(reg_buttons, 1)
        update.message.reply_text(
            "Приступим к платежам!", reply_markup=reg_markup
        )
        return MAKE_PAYMENT


def check_user_first_name(update, context):
    global _user_last_name

    user_message = update.message.text

    if user_message == "Согласен":
        telegram_user = update.effective_user
        user_first_name = telegram_user.first_name or ""
        _user_last_name = telegram_user.last_name or ""

        user_first_name_buttons = [user_first_name]
        user_first_name_markup = keyboard_maker(user_first_name_buttons, 2)
        context.user_data["user_first_name_markup"] = user_first_name_markup
        update.message.reply_text(
            "Введите Ваше имя или нажмите кнопку ниже:",
            reply_markup=user_first_name_markup,
            parse_mode="HTML",
        )
        return USER_LAST_NAME
    else:
        bot = context.bot
        bot.send_message(
            chat_id=update.callback_query.from_user.id,
            text="Всего Вам хорошего!",
        )
        return ConversationHandler.END


def check_user_last_name(update, context):
    global _user_last_name

    user_message = update.message.text
    context.user_data["first_name"] = user_message
    message_text = f"Вы ввели имя: {user_message}"
    update.message.reply_text(message_text)

    user_last_name_buttons = [_user_last_name]
    user_last_name_markup = keyboard_maker(user_last_name_buttons, 2)
    context.user_data["user_last_name_buttons"] = user_last_name_buttons
    update.message.reply_text(
        "Введите Вашу фамилию или нажмите кнопку ниже:",
        reply_markup=user_last_name_markup,
        parse_mode="HTML",
    )
    return USER_PHONE_NUMBER


def check_user_phone_number(update, context):
    user_message = update.message.text
    context.user_data["last_name"] = user_message
    message_text = f"Вы ввели фамилию: {user_message}"
    update.message.reply_text(message_text)

    contact_keyboard = KeyboardButton(
        text="Отправить номер телефона", request_contact=True
    )
    reply_markup = ReplyKeyboardMarkup(
        [[contact_keyboard]], resize_keyboard=True
    )
    update.message.reply_text(
        "Нажмите кнопку ниже или введите Ваш номер телефона в формате +71231234567",
        reply_markup=reply_markup,
    )
    return USER_PASSPORT_ID


def get_contact(update, context):
    text = ""
    if update.message.contact:
        text += str(update.message.contact.phone_number)
    phone_buttons = [text]
    phone_markup = keyboard_maker(phone_buttons, 2)
    update.message.reply_text(
        "Нажмите кнопку с Вашим номером телефона внизу для подтверждения",
        reply_markup=phone_markup,
    )
    return USER_PASSPORT_ID


def check_user_passport_id(update, context):
    user_message = update.message.text
    context.user_data["phone_number"] = user_message
    message_text = f"Вы ввели номер телефона: {user_message}"
    update.message.reply_text(message_text)
    try:
        checking_number = phonenumbers.parse(user_message)
    except phonenumbers.NumberParseException as npe:
        checking_number = phonenumbers.parse("+7{}".format(user_message))

    if phonenumbers.is_valid_number(checking_number):
        update.message.reply_text(
            "Введите Ваш паспорт в формате 1122 123456:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return USER_BIRTHDAY
    else:
        update.message.reply_text(
            "Телефон введен неверно! Введите Ваш номер телефона в формате +71231234567:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return USER_PASSPORT_ID


def check_user_birthdate(update, context):
    user_message = update.message.text
    context.user_data["passport_id"] = user_message
    message_text = f"Вы ввели паспортные данные: {user_message}"
    update.message.reply_text(message_text)
    if re.match("\d{4}\s\d{6}$", user_message):
        update.message.reply_text(
            "Введите Вашу дату рождения в формате дд.мм.гггг:",
            parse_mode="HTML",
        )
        return SAVE_USER
    else:
        update.message.reply_text(
            "Паспортные данные введены неверно! Введите Ваш паспорт в формате 1122 123456:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return USER_BIRTHDAY


def save_user_attributes(update, context):
    user_message = update.message.text
    context.user_data["birthday"] = user_message
    message_text = f"Вы ввели дату рождения: {user_message}"
    update.message.reply_text(message_text)
    date_matched = True
    try:
        regex = datetime.strptime
        assert regex(user_message, "%d.%m.%Y")
    except ValueError as e:
        date_matched = False

    if date_matched:
        user_message = update.message.text
        context.user_data["birthday"] = str(
            datetime.strptime(user_message, "%d.%m.%Y").strftime("%Y-%m-%d")
        )

        customer = save_customer(context)
        context.user_data["customer"] = customer

        update.message.reply_text(
            "Ваши данные сохранены в базе",
            parse_mode="HTML",
        )
        reg_buttons = ["Далее"]
        reg_markup = keyboard_maker(reg_buttons, 1)
        update.message.reply_text(
            "Приступим к платежам!", reply_markup=reg_markup
        )
        return MAKE_PAYMENT
    else:
        update.message.reply_text(
            "Дата рождения введена неверно! Введите Вашу дату рождения в формате дд.мм.гггг:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return SAVE_USER


def make_payment(update, context):
    price = int(context.user_data["price"]) * 100
    chat_id = update.message.chat_id
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendInvoice"
    payload = {
        "chat_id": chat_id,
        "title": "Бронирование склада",
        "description": "Описание",
        "payload": "payload",
        "provider_token": ukassa_token,
        "currency": "RUB",
        "start_parameter": "test",
        "prices": json.dumps([{"label": "Руб", "amount": price}]),
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()

    reg_buttons = ["Новый заказ", "Мои заказы"]
    reg_markup = keyboard_maker(reg_buttons, 1)
    update.message.reply_text("Оплатите заказ", reply_markup=reg_markup)
    return CATCH_PAYMENT


def catch_payment(update, context):
    pre_checkout_query_id = update["pre_checkout_query"]["id"]
    context.bot.answer_pre_checkout_query(pre_checkout_query_id, ok=True)

    return CREATE_QR


def create_qr(update, context):
    code = random.randint(100000, 999999)
    filename = f"{code}.png"
    img = qrcode.make(code)
    img.save(filename)

    save_order(context)

    chat_id = update.message.chat_id
    bot.send_message(
        chat_id=chat_id,
        text="Данные по заказу сохранены! Получите Ваш QR-код для доступа к складу!",
    )
    with open(filename, "rb") as file:
        bot.send_photo(chat_id=chat_id, photo=open(filename, "rb"))
    os.remove(filename)
    bot.send_message(chat_id=chat_id, text="Всего Вам хорошего!")

    # return ???


def end(update, context):
    bot = context.bot
    bot.send_message(
        chat_id=update.callback_query.from_user.id, text="Всего Вам хорошего!"
    )
    return ConversationHandler.END


class Command(BaseCommand):
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        # updater = Updater(bot=bot, use_context=True)
        updater = Updater(TG_TOKEN, use_context=True)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                WAREHOISES: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.location, get_location),
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
                    MessageHandler(Filters.text, get_period),
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
                CHOICE_PERIOD: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, choice_period),
                ],
                CHECK_USER: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, check_register_user),
                ],
                USER_FIRST_NAME: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, check_user_first_name),
                ],
                USER_LAST_NAME: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, check_user_last_name),
                ],
                USER_PHONE_NUMBER: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, check_user_phone_number),
                ],
                USER_PASSPORT_ID: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, check_user_passport_id),
                ],
                USER_BIRTHDAY: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, check_user_birthdate),
                ],
                SAVE_USER: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, save_user_attributes),
                ],
                MAKE_PAYMENT: [
                    CommandHandler("start", start),
                    MessageHandler(Filters.text, make_payment),
                ],
            },
            fallbacks=[CommandHandler("end", end)],
        )

        updater.dispatcher.add_handler(
            MessageHandler(Filters.successful_payment, create_qr)
        )
        updater.dispatcher.add_handler(conv_handler)
        updater.dispatcher.add_handler(PreCheckoutQueryHandler(catch_payment))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.contact, get_contact)
        )

        updater.start_polling()
        updater.idle()
