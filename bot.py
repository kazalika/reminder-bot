import logging
import telegramcalendar
from datetime import datetime, timedelta
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import json
import random
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

NAME, DATE_Q, TIME_Q, INFO, OPT = range(5)
UTC_1, UTC_2 = range(2)


def json_editor(user, key, value):
    user = str(user)
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        if user not in content["reminder"].keys():
            content["reminder"][user] = {"utc": 0, "reminder": []}
        if key == "name":
            content["reminder"][user]["reminder"].insert(0, {})
        content["reminder"][user]["reminder"][0][key] = value
        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_getter(user, ):
    with open("reminder.json") as file:
        content = json.load(file)
        element = content["reminder"][user]["reminder"][0]
        name = element["name"]
        date = element["date"]
        _time = element["time"]
        r_id = element["id"]
        return name, date, _time, r_id


def json_deleter(user, r_id=None, current=False):
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        reminder = content["reminder"][user]["reminder"]
        if not current:
            for i in range(len(reminder)):
                if reminder[i]["id"] == r_id:
                    del reminder[i]
                    break
        else:
            del reminder[0]
        file.seek(0)
        json.dump(content, file)
        file.truncate()


def json_utc(user, utc=None):
    with open("reminder.json", "r+") as file:
        content = json.load(file)
        if utc is None:
            return content["reminder"][user]["utc"]
        else:
            content["reminder"][user]["utc"] = utc
            file.seek(0)
            json.dump(content, file)
            file.truncate()


def all_reminder(update, context):
    reply_keyboard = [["/start", "/list", "/time"]]
    username = str(update.message["chat"]["id"])
    with open("reminder.json") as file:
        content = json.load(file)
        reminder = content["reminder"][username]["reminder"]
        if len(reminder) == 0:
            update.message.reply_text(f"\U0001F4C3 * Список напоминаний * \U0001F4C3\n\nУ вас нет никаких напоминаний!", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True), parse_mode="markdown")
        else:
            update.message.reply_text("\U0001F4CB* Список напоминаний *\U0001F4CB", parse_mode="markdown")
            for i, v in enumerate(reminder):
                name = v["name"]
                date = v["date"]
                _time = v["time"]
                if "opt_inf" in v.keys():
                    information = v["opt_inf"]
                    if i == len(reminder) - 1:
                        update.message.reply_text(f"{i+1}:   Название: {name}\n      Дата: {date}\n      Время: {_time}\n      Описание: {information}", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
                    else:
                        update.message.reply_text(f"{i+1}:   Название: {name}\n      Дата: {date}\n      Время: {_time}\n      Описание: {information}")
                else:
                    if i == len(reminder) - 1:
                        update.message.reply_text(f"{i+1}:   Название: {name}\n      Дата: {date}\n      Время: {_time}", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
                    else:
                        update.message.reply_text(f"{i+1}:   Название: {name}\n      Дата: {date}\n      Время: {_time}")


def utc_time(update, context):
    update.message.reply_text("Выберите часовой пояс, в котором живете", reply_markup=telegramcalendar.create_timezone())
    return UTC_1


def utc_time_selector(update, context):
    reply_keyboard = [["/start", "/list", "/time"]]
    selected, num = telegramcalendar.process_utc_selection(context.bot, update)
    if selected:
        chat_id = str(update.callback_query.from_user.id)
        json_utc(chat_id, utc=num)
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text=f"Вы выбрали UTC + {num}" if num >= 0 else f"Вы выбрали UTC - {abs(num)}",
                        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        return ConversationHandler.END


def notification(context):
    reply_keyboard = [["/start", "/list", "/time"]]
    job = context.job
    if len(job.context) == 6:
         name, date, _time, username, r_id = job.context[1], job.context[2], job.context[3], job.context[4], job.context[5]
         context.bot.send_message(job.context[0], text=f"\U0001F4A1* Напоминание *\U0001F4A1\n\nНазвание: {name}\nУстановлен на {date} - {_time}.\nВыполнится через 10 минут!", parse_mode="markdown")
    else:
        name, date, _time, username, r_id, information = job.context[1], job.context[2], job.context[3], job.context[4], job.context[5], job.context[6]
        context.bot.send_message(job.context[0], text=f"\U0001F4A1* Напоминание *\U0001F4A1\n\nНазвание: {name}\nОписание: {information}\n\nУстановлен на {date} - {_time}.\nВыполнится через 10 минут!", parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
    json_deleter(username, r_id=r_id)


def start(update, context):
    # print(update.message)
    update.message.reply_text("*\U0001F4CD Давайте установим напоминание *\U0001F4CD\n\nКак назовете это напоминание?", parse_mode="markdown")
    # update.message.reply_text(f"test", reply_markup=telegramcalendar.create_clock(), parse_mode="markdown")
    return NAME


def name(update, context):
    name = update.message.text
    if name == "/cancel":
        cancel(update, context)
        return ConversationHandler.END
    username = update.message["chat"]["id"]
    json_editor(username, "name", name)
    logger.info("Name: %s", update.message.text)
    update.message.reply_text(f"\U0001F4C5* Установка *\U0001F4C5\n\nКогда вы хотите получить напоминание\nпо *{name}*?",
                              reply_markup=telegramcalendar.create_calendar(), parse_mode="markdown")
    return DATE_Q


def inline_handler(update, context):
    selected, date = telegramcalendar.process_calendar_selection(context.bot, update)
    if selected:
        json_editor(str(update.callback_query.from_user.id), "date", date.strftime("%d/%m/%Y"))
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="Вы выбрали %s" % (date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())
        context.bot.send_message(chat_id=update.callback_query.from_user.id, text="\U0001F553* Установка *\U0001F553\n\nКогда вы хотите получить напоминание?", parse_mode="markdown", reply_markup=telegramcalendar.create_clock(user=update.callback_query.from_user.id))
        return TIME_Q


def inline_handler2(update, context):
    selected, _time = telegramcalendar.process_clock_selection(context.bot, update)
    if selected:
        chat_id = str(update.callback_query.from_user.id)
        r_id = random.randint(0, 100000)
        format_time = f"{_time[0]}:{_time[1]} {_time[2]}"
        json_editor(chat_id, "time", format_time)
        json_editor(chat_id, "id", r_id)

        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                 text=f"Вы выбрали {format_time}",
                                 reply_markup=ReplyKeyboardRemove())
        reply_keyboard = [["Да", "Нет"]]
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                                text=f"\U0001F530 *Установлено* \U0001F530\n\nХотите добавить описание?",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True), parse_mode="markdown")
        return INFO


def info(update, context):
    text = update.message.text
    if text == "Да":
        update.message.reply_text(f"\U00002139 *Установлено* \U00002139\n\nОтправьте описание для напоминания!", parse_mode="markdown")
        return OPT
    else:
        reply_keyboard = [["/start", "/list", "/time"]]
        chat_id = str(update.message["chat"]["id"])
        name, date, format_time, r_id = json_getter(chat_id)
        num = json_utc(chat_id)
        hour, minute, m = int(format_time.split(" ")[0].split(":")[0]), int(format_time.split(" ")[0].split(":")[1]), format_time.split(" ")[1]

        if "pm" in m:
            n_hour = hour + 12
        else:
            n_hour = hour

        seconds = datetime.timestamp(datetime.strptime(date, "%d/%m/%Y") + timedelta(hours=n_hour, minutes=minute)) - (datetime.timestamp(datetime.now()) + (num * 3600))
        print(seconds)
        if seconds < 0:
            context.bot.send_message(chat_id=chat_id, text=f"\U0000274C*Ошибка*\U0000274C\n\nВы указали дату из прошлого.\nВыберите валидную дату!", parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
            json_deleter(chat_id, r_id=r_id)
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text=f"*\U0001F4CC Сохранено напоминание *\U0001F4CC\n\nНазвание: {name}\nДата: {date}\nВремя: {hour}:{minute} {m}",
                                     parse_mode="markdown",
                                     reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                      resize_keyboard=True))
            context.job_queue.run_once(notification, seconds, context=[chat_id, name, date, format_time, chat_id, r_id], name=chat_id)
        return ConversationHandler.END


def opt_info(update, context):
    reply_keyboard = [["/start", "/list", "/time"]]
    information = update.message.text
    chat_id = str(update.message["chat"]["id"])
    json_editor(chat_id, "opt_inf", information)
    name, date, format_time, r_id = json_getter(chat_id)
    num = json_utc(chat_id)
    hour, minute, m = int(format_time.split(" ")[0].split(":")[0]), int(format_time.split(" ")[0].split(":")[1]), format_time.split(" ")[1]

    if "pm" in m:
        n_hour = hour + 12
    else:
        n_hour = hour

    seconds = datetime.timestamp(datetime.strptime(date, "%d/%m/%Y") + timedelta(hours=n_hour, minutes=minute)) - (datetime.timestamp(datetime.now()) + (num * 3600))
    print(seconds)
    if seconds < 0:
        context.bot.send_message(chat_id=chat_id, text=f"\U0000274C*Ошибка*\U0000274C\n\nВы указали дату из прошлого.\nВыберите валидную дату!", parse_mode="markdown", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        json_deleter(chat_id, r_id=r_id)
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text=f"*\U0001F4CC Напоминание поставлено *\U0001F4CC\n\nНазвание: {name}\nДата: {date}\nВремя: {hour}:{minute} {m}",
                                 parse_mode="markdown",
                                 reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                  resize_keyboard=True))
        context.job_queue.run_once(notification, seconds, context=[chat_id, name, date, format_time, chat_id, r_id, information], name=chat_id)
    return ConversationHandler.END


def cancel(update, context):
    username = str(update.message["chat"]["id"])
    logger.info("User %s canceled the reminder setup.", username)
    json_deleter(username, current=True)
    update.message.reply_text('\U0001F53A *Отмена установки* \U0001F53A'
                              '\n\nВы удалили все напоминания', reply_markup=ReplyKeyboardRemove(), parse_mode="markdown")
    return ConversationHandler.END


def main():
    updater = Updater("5938398331:AAH9Zq6ld6fiEpIVfdWTlq5ni-vFgk0KxYA", use_context=True)

    dp = updater.dispatcher

    all_reminder_handler = CommandHandler("list", all_reminder)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text, name)],
            DATE_Q: [CallbackQueryHandler(inline_handler)],
            TIME_Q: [CallbackQueryHandler(inline_handler2)],
            INFO: [MessageHandler(Filters.text, info)],
            OPT: [MessageHandler(Filters.text, opt_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    conv_handler_utc = ConversationHandler(
        entry_points=[CommandHandler("time", utc_time)],
        states={
            UTC_1: [CallbackQueryHandler(utc_time_selector)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(all_reminder_handler)

    dp.add_handler(conv_handler)

    dp.add_handler(conv_handler_utc)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()