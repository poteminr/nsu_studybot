import json
import datetime, pytz
import logging
import telegram.error
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from scripts.bot_functions import write_data, read_data, get_seminar_number_by_time
from scripts.schedule_api import get_group_seminars, get_group_id

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]

SUBJECT = range(1)


def start(update: Update, _: CallbackContext):
    text_part_one = "Привет, это StudyBot, отправляй изображение или текст домашней работы!\n\n"
    text_part_two = "Для начала добавьте номер своей группы.\n"
    text_part_three = "Для корректное работы в группе необходимы админ-права.\n"

    text = text_part_one + text_part_two + text_part_three
    update.message.reply_text(text,
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                               resize_keyboard=True))
    update.message.reply_photo(photo=open("./studybot_info.png", 'rb'))


def restart(update: Update, _: CallbackContext):
    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.first_name)

    text = "Бот перезагружен!"
    update.message.reply_text(text,
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                               resize_keyboard=True))

    return ConversationHandler.END


def init_user_group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)

    try:
        get_group_id(user_group)
        write_data(user_id, 'group', user_group)
        update.message.reply_text(f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново.")
    except KeyError:
        write_data(user_id, 'group', 228)
        update.message.reply_text(f"Группа {user_group} не найдена, используйте команду еще раз.")


def add(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    date = update.message.date

    user_group = read_data(user_id)

    if user_group is not None:
        if len(update.message.photo) == 0:
            is_photo = False
            message = update.message.text.split("/add")[1].strip()
        else:
            is_photo = True
            file_id = update.message.photo[-1]['file_id']

        field = get_seminar_number_by_time(user_id, date)

        if field is not None:
            if is_photo:
                write_data(user_id, field, file_id)

                update.message.reply_text(f'Фотография "{field}" успешно загружена!',
                                          reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                           resize_keyboard=True))
            else:
                write_data(user_id, field, message)

                update.message.reply_text(f'Текст "{field}" успешно загружен!',
                                          reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                           resize_keyboard=True))
        else:
            update.message.reply_text(f'Занятия сейчас нет. Попробуйте добавить вручную!',
                                      reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                       resize_keyboard=True))

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def view_assigment(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = read_data(user_id)

    if user_group is not None:

        context.user_data['command_to_view_mes_id'] = update.message['message_id']
        context.user_data['command_to_view_chat_id'] = update.message.chat['id']

        subjects, _ = get_group_seminars(user_group['group'])
        value = len(subjects)

        part_one = subjects[:int(value / 3)]
        part_two = subjects[int(value / 3):int(value / 3) * 2]
        part_three = subjects[int(value / 3) * 2:]

        keyboard = [part_one, part_two, part_three]

        sent_message = update.message.reply_text(f'Выберите необходимый предмет.',
                                                 reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True,
                                                                                  resize_keyboard=True))

        context.user_data['bot_rep_to_view_mes_id'] = sent_message['message_id']

        return SUBJECT

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def show_assigment(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_data = read_data(user_id)

    field = update.message.text

    if field in user_data.keys():
        data = user_data[field]
        try:
            update.message.reply_photo(data, reply_markup=ReplyKeyboardRemove())
            update.message.reply_text(f'Удачи с "{field}" ❤️!',
                                      reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                       resize_keyboard=True))
        except telegram.error.BadRequest:
            update.message.reply_text(data, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                             resize_keyboard=True))

    else:
        update.message.reply_text(f'Данные "{field}" отсутствуют.',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                   resize_keyboard=True))

    update.message.bot.delete_message(context.user_data['command_to_view_chat_id'],
                                      context.user_data['command_to_view_mes_id'])

    update.message.bot.delete_message(context.user_data['command_to_view_chat_id'],
                                      context.user_data['bot_rep_to_view_mes_id'])

    return ConversationHandler.END


FIELD, ADDED = range(2)


def add_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = read_data(user_id)

    if user_group is not None:
        context.user_data['command_to_add_mes_id_1'] = update.message['message_id']
        context.user_data['command_to_add_chat_id'] = update.message.chat['id']

        subjects, _ = get_group_seminars(user_group['group'])
        value = len(subjects)

        part_one = subjects[:int(value / 3)]
        part_two = subjects[int(value / 3):int(value / 3) * 2]
        part_three = subjects[int(value / 3) * 2:]

        keyboard = [part_one, part_two, part_three]

        sent_message = update.message.reply_text(f'Выберите необходимый предмет.',
                                                 reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True,
                                                                                  resize_keyboard=True))

        context.user_data['reply_to_add_mes_id_1'] = sent_message['message_id']

        return FIELD

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def pick_field_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']

    context.user_data['command_to_add_mes_id_2'] = update.message['message_id']

    field = update.message.text
    context.user_data['choice'] = field
    sent_message = update.message.reply_text(f'Отправьте фотографию или текст! Не забудьте добавить /add.')

    context.user_data['reply_to_add_mes_id_2'] = sent_message['message_id']

    return ADDED


def load_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']

    if len(update.message.photo) == 0:
        is_photo = False
        message = update.message.text.split("/add")[1].strip()
    else:
        is_photo = True
        file_id = update.message.photo[-1]['file_id']

    field = context.user_data['choice']

    if is_photo:
        write_data(user_id, field, file_id)

        update.message.reply_text(f'Фотография "{field}" успешно загружена!',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))
    else:
        write_data(user_id, field, message)

        update.message.reply_text(f'Текст "{field}" успешно загружен!',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))

    update.message.bot.delete_message(context.user_data['command_to_add_chat_id'],
                                      context.user_data['command_to_add_mes_id_1'])
    update.message.bot.delete_message(context.user_data['command_to_add_chat_id'],
                                      context.user_data['reply_to_add_mes_id_1'])

    update.message.bot.delete_message(context.user_data['command_to_add_chat_id'],
                                      context.user_data['command_to_add_mes_id_2'])
    update.message.bot.delete_message(context.user_data['command_to_add_chat_id'],
                                      context.user_data['reply_to_add_mes_id_2'])

    return ConversationHandler.END


def send_user_data(update: Update, _: CallbackContext):
    owner_id = -445717352
    password = update.message.text.split(" ")[1]

    with open('keys.json') as f:
        keys = json.load(f)

    if keys['backup_password'] == password:
        data = open('./data.json', 'rb')
        filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ".json"

        update.message.bot.sendDocument(chat_id=owner_id, document=data, filename=filename)


def backup_every_day(context: CallbackContext):
    print("data")
    owner_id = -445717352
    data = open('./data.json', 'rb')
    filename = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') + ".json"

    context.bot.sendDocument(chat_id=owner_id, document=data, filename=filename)


def main():
    with open('keys.json') as f:
        keys = json.load(f)

    updater = Updater(token=keys['token'], use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("group", init_user_group))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Просмотреть домашние задания$'), view_assigment)],
        states={
            SUBJECT: [MessageHandler(Filters.text & ~(Filters.command), show_assigment)]
        },
        fallbacks=[CommandHandler('restart', restart)]
    )

    dispatcher.add_handler(conv_handler)

    conv_handler_two = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Добавить задание вручную$'), add_by_hand)],
        states={
            FIELD: [MessageHandler(Filters.text & ~(Filters.command), pick_field_by_hand)],
            ADDED: [MessageHandler(Filters.photo & Filters.caption('^/add$'), load_by_hand),
                    CommandHandler("add", load_by_hand)]
        },
        fallbacks=[CommandHandler('restart', restart)]
    )

    dispatcher.add_handler(conv_handler_two)
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.caption('^/add$'), add))
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("restart", restart))
    dispatcher.add_handler(CommandHandler("backup", send_user_data))

    updater.job_queue.run_daily(backup_every_day, time=datetime.time(23, 00, 00, tzinfo=pytz.timezone('Asia/Novosibirsk')))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
