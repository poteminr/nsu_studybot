import json
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from scripts.bot_functions import write_data, read_data, get_seminar_number_by_time
from scripts.schedule_api import get_group_seminars, get_group_id

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]

SUBJECT = range(1)


def start(update: Update, _: CallbackContext):
    text_part_one = "Привет, это StudyBot, отправляй изображение домашней работы и мы составим личное расписание!\n"
    text_part_two = "Введите номер группы '/group номер', чтобы начать работу!\n"
    text_part_three = "Добавляйте /add как подпись к фото!\n"
    text_part_four = "Для корректное работы в группе необходимы админ-права.\n"
    update.message.reply_text(text_part_one + text_part_two + text_part_three + text_part_four,
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                               resize_keyboard=True))


def restart(update: Update, _: CallbackContext):
    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.first_name)

    text = "Бот перезагружен!"
    update.message.reply_text(text,
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                               resize_keyboard=True))

    return ConversationHandler.END


def group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)

    try:
        get_group_id(user_group)
        write_data(user_id, 'group', user_group)
        update.message.reply_text(f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново.")
    except KeyError:
        write_data(user_id, 'group', user_group)
        update.message.reply_text(f"Группа {user_group} не найдена, используйте команду еще раз.")


def add(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    date = update.message.date
    file_id = update.message.photo[-1]['file_id']

    logger.info("Photo of %s: %s", user.first_name, file_id)
    field = get_seminar_number_by_time(user_id, date)

    if field is not None:
        write_data(user_id, field, file_id)

        update.message.reply_text(f'Фотография "{field}" успешно загружена!',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))
    else:
        update.message.reply_text(f'Занятия сейчас нет. Попробуйте добавить фото вручную!',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def view(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']

    context.user_data['command_to_view_mes_id'] = update.message['message_id']
    context.user_data['command_to_view_chat_id'] = update.message.chat['id']

    subjects, _ = get_group_seminars(user_group)
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


def show(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_data = read_data(user_id)

    field = update.message.text

    if field in user_data.keys():

        file_id = user_data[field]

        update.message.reply_photo(file_id, reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(f'Удачи с "{field}" ❤️!',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
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
    user_group = read_data(user_id)['group']

    context.user_data['command_to_add_mes_id_1'] = update.message['message_id']
    context.user_data['command_to_add_chat_id'] = update.message.chat['id']

    subjects, _ = get_group_seminars(user_group)
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


def pick_field_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']

    context.user_data['command_to_add_mes_id_2'] = update.message['message_id']

    field = update.message.text
    context.user_data['choice'] = field
    sent_message = update.message.reply_text(f'Отправьте фотографию! Не забудьте добавить /add.')

    context.user_data['reply_to_add_mes_id_2'] = sent_message['message_id']

    return ADDED


def load_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    file_id = update.message.photo[-1]['file_id']

    logger.info("Photo of %s: %s", user.first_name, file_id)

    field = context.user_data['choice']

    write_data(user_id, field, file_id)

    update.message.reply_text(f'Фотография "{field}" успешно загружена!',
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


def main():
    with open('keys.json') as f:
        keys = json.load(f)

    updater = Updater(token=keys['token'], use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("group", group))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Просмотреть домашние задания$'), view)],
        states={
            SUBJECT: [MessageHandler(Filters.text & ~(Filters.command), show)]
        },
        fallbacks=[CommandHandler('restart', restart)]
    )

    dispatcher.add_handler(conv_handler)

    conv_handler_two = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Добавить задание вручную$'), add_by_hand)],
        states={
            FIELD: [MessageHandler(Filters.text & ~(Filters.command), pick_field_by_hand)],
            ADDED: [MessageHandler(Filters.photo & Filters.caption('^/add$'), load_by_hand)]
        },
        fallbacks=[CommandHandler('restart', restart)]
    )

    dispatcher.add_handler(conv_handler_two)
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.caption('^/add$'), add))
    dispatcher.add_handler(CommandHandler("restart", restart))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
