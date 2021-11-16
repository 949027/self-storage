import os
from environs import Env
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram.utils.request import Request


from ugc.models import (
    Customers,
    OrderStatuses,
    Levels,
    Forms,
    Topping,
    Berries,
    Decors,
    Orders,
)

# (
#     FIRST,
#     COMMENTS,
#     DELIVERY_ADDRESS,
#     DELIVERY_DATE,
#     ORDER_CAKE,
#     END,
#     REGISTER_ADDRESS,
#     REGISTER_PHONE,
#     START_AFTER_REG,
# ) = range(9)
# (
#     LEVELS,
#     EXIT,
#     COMPLITED_ORDERS,
#     START_OVER,
#     DELIVERY_TIME,
#     FORM,
#     TOPPING,
#     BERRIES,
#     DECOR,
#     TITLE,
#     COMMENTS,
#     SHOW_COST,
#     INPUT_LEVELS,
#     START,
# ) = range(14)


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
def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Собрать торт", callback_data=str(LEVELS)),
            InlineKeyboardButton(
                "Сделанные заказы", callback_data="COMPLITED_ORDERS"
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot = context.bot

    bot.send_message(
        chat_id=update.message.chat_id,
        text="Выберите действие:",
        reply_markup=reply_markup,
    )


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
        env = Env()
        env.read_env()
        TG_TOKEN = env.str("TG_TOKEN")

        request = Request(connect_timeout=0.5, read_timeout=1.0)
        bot = Bot(
            request=request,
            token=TG_TOKEN,
            base_url=getattr(settings, "PROXY_URL", None),
        )

        updater = Updater(bot=bot, use_context=True)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            fallbacks=[CommandHandler("end", end)],
        )

        updater.dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
