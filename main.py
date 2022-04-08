from scripts.bot_functions import write_data, read_data, get_seminar_number_by_time, university_codes2text, \
    university_codes2city
from scripts.schedule_api import get_group_seminars, get_group_id
from scripts.private_keys import import_private_keys
import logging
import telegram.error
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler, Filters,
    ConversationHandler,
    CallbackQueryHandler
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUBJECT = range(1)
FIRST, SECOND = range(2)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]


def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    update.message.reply_photo(photo=open("images/studybot_info.png", 'rb'), reply_markup=ReplyKeyboardRemove())

    keyboard = [
        [InlineKeyboardButton("Новосибирск", callback_data=str(1))],

        [InlineKeyboardButton("Москва", callback_data=str(2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите свой город 🏢", reply_markup=reply_markup)

    return FIRST


def start_over(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("Новосибирск", callback_data=str(1))],
        [InlineKeyboardButton("Москва", callback_data=str(2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой город 🏢", reply_markup=reply_markup)

    return FIRST


def choose_university_nsk(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("НГУ", callback_data=str(1.1))],
        [InlineKeyboardButton("НГТУ", callback_data=str(1.2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой университет 🧑🏻‍🎓", reply_markup=reply_markup)

    return FIRST


def choose_university_msk(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("МГУ", callback_data=str(2.1))],
        [InlineKeyboardButton("МГТУ", callback_data=str(2.2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой университет 🧑🏻‍🎓", reply_markup=reply_markup)

    return FIRST


def confirm_choice_of_university(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat.id
    write_data(user_id, 'university_code', query.data)
    write_data(user_id, 'city', university_codes2city(query.data))

    keyboard = [
        [
            InlineKeyboardButton("Выбрать еще раз", callback_data=str(1)),
            InlineKeyboardButton("Подтвердить", callback_data=str(2)),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Вы выбрали {university_codes2text(query.data)}. Всё верно?",
                            reply_markup=reply_markup)

    return SECOND


def university_selection_end(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    query.edit_message_text(text="Университет выбран! \nТеперь используйте '/group номер вашей группы'")

    return ConversationHandler.END


def restart(update: Update, _: CallbackContext):
    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.first_name)

    update.message.reply_text(text="Бот перезагружен!")

    return ConversationHandler.END


def init_user_group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)

    try:
        get_group_id(user_group)
        write_data(user_id, 'group', user_group)

        text = f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново."
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                         resize_keyboard=True))
    except KeyError:
        write_data(user_id, 'group', -1)
        update.message.reply_text(f"Группа {user_group} не найдена, используйте команду еще раз.", )


# TODO: Refactor and optimize this function
def add(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    date = update.message.date

    user_group = read_data(user_id)
    reply_murkup_keyboard = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

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
                                          reply_markup=reply_murkup_keyboard)
            else:
                write_data(user_id, field, message)

                update.message.reply_text(f'Текст "{field}" успешно загружен!',
                                          reply_markup=reply_murkup_keyboard)
        else:
            update.message.reply_text(f'Занятия сейчас нет. Попробуйте добавить вручную!',
                                      reply_markup=reply_murkup_keyboard)

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=reply_murkup_keyboard)


def view_assigment(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = read_data(user_id)

    if user_group is not None:

        context.user_data['command_to_view_message_id'] = update.message['message_id']
        context.user_data['command_to_view_chat_id'] = update.message.chat['id']

        subjects, _ = get_group_seminars(user_group['group'])
        subjects = sorted(subjects)

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(ind))] for ind, seminar_name in
                    enumerate(subjects)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text("Выберите необходимый предмет", reply_markup=reply_markup)

        return SUBJECT

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def send_assigment_to_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.message.chat.id

    user_data = read_data(user_id)

    field_index = query.data
    field_text = query.message.reply_markup.inline_keyboard[int(field_index)][0]['text']

    if field_text in user_data.keys():
        data = user_data[field_text]
        try:
            update.callback_query.message.reply_photo(data, caption=f"{field_text}")
            query.delete_message()

        except telegram.error.BadRequest:
            query.edit_message_text(text=f"{field_text}: \n{data}")

    else:
        query.edit_message_text(text=f'Данные по предмету: \n"{field_text}" \nотсутствуют.')

    update.callback_query.message.bot.delete_message(context.user_data['command_to_view_chat_id'],
                                                     context.user_data['command_to_view_message_id'])

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
        subjects = sorted(subjects)

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(ind))] for ind, seminar_name in
                    enumerate(subjects)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(f'Выберите необходимый предмет', reply_markup=reply_markup)

        return FIELD

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def pick_field_by_hand(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    field_index = query.data
    field_text = query.message.reply_markup.inline_keyboard[int(field_index)][0]['text']
    context.user_data['user_filed_choice'] = field_text

    query.edit_message_text(text=f"Отправьте фотографию или текст! Не забудьте добавить /add.")

    return ADDED


def load_by_hand(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    if len(update.message.photo) == 0:
        is_photo = False
        message = update.message.text.split("/add")[1].strip()
    else:
        is_photo = True
        file_id = update.message.photo[-1]['file_id']

    field = context.user_data['user_filed_choice']

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

    return ConversationHandler.END


def main():
    API_KEY = import_private_keys(json_path='keys.json', key_name='token')

    updater = Updater(token=API_KEY, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("group", init_user_group))

    conv_handler_pick_university = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [
                CallbackQueryHandler(choose_university_nsk, pattern='^' + str(1) + '$'),
                CallbackQueryHandler(choose_university_msk, pattern='^' + str(2) + '$'),
                CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(1.1) + '$'),
                CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(1.2) + '$'),
                CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(2.1) + '$'),
                CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(2.2) + '$'),
            ],
            SECOND: [
                CallbackQueryHandler(start_over, pattern='^' + str(1) + '$'),
                CallbackQueryHandler(university_selection_end, pattern='^' + str(2) + '$'),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler_pick_university)

    conv_handler_view_assigment = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Просмотреть домашние задания$'), view_assigment)],
        states={
            SUBJECT: [
                CallbackQueryHandler(send_assigment_to_user),
            ],

        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler_view_assigment)


    conv_handler_add_assigment_by_hand = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Добавить задание вручную$'), add_by_hand)],
        states={
            FIELD: [CallbackQueryHandler(pick_field_by_hand)],
            ADDED: [MessageHandler(Filters.photo & Filters.caption('^/add$'), load_by_hand),
                    CommandHandler("add", load_by_hand)]

        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler_add_assigment_by_hand)
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.caption('^/add$'), add))
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("restart", restart))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
