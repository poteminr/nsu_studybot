from scripts.schedule_api import get_group_seminars
from scripts.bot_functions import read_data, generate_dates_of_future_seminars, write_data
from registration import start
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler, Filters,
    ConversationHandler,
    CallbackQueryHandler
)

FIELD, TIME_TYPE, DATE = range(3)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]


def add_assignment(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']
    context.user_data['user_group'] = user_group

    if user_group is not None:
        context.user_data['command_to_add_mes_id_1'] = update.message['message_id']
        context.user_data['command_to_add_chat_id'] = update.message.chat['id']

        subjects, _, seminars_weekdays = get_group_seminars(user_group)
        subjects = sorted(subjects)

        context.user_data['seminars_weekdays'] = seminars_weekdays

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(ind))] for ind, seminar_name in
                    enumerate(subjects)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(f'Выберите необходимый предмет', reply_markup=reply_markup)

        return FIELD

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def choose_time_type_of_assignment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    field_index = query.data
    field_text = query.message.reply_markup.inline_keyboard[int(field_index)][0]['text']
    context.user_data['user_field_choice'] = field_text

    keyboard = [
        [InlineKeyboardButton("Добавить задание на будущие занятия ", callback_data='future_seminars')],
        [InlineKeyboardButton("Изменить задание прошедших занятий", callback_data='past_seminars')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Выберите дату занятия.", reply_markup=reply_markup)

    return TIME_TYPE


def choose_assignment_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    field_text = context.user_data['user_field_choice']
    time_index = query.data
    date = query.message.date

    seminar_weekdays = context.user_data['seminars_weekdays'][field_text]

    keyboard = None
    if time_index == "future_seminars":
        future_seminars_dates = generate_dates_of_future_seminars(date, seminar_weekdays)

        buttons = [InlineKeyboardButton(date, callback_data=date) for date in future_seminars_dates]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

    elif time_index == "past_seminars":
        raise NotImplemented

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите дату занятия.", reply_markup=reply_markup)

    return DATE


def process_seminar_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    date = query.data
    context.user_data['seminar_date'] = date

    query.edit_message_text(text=f"Отправьте фотографию или текст! Не забудьте добавить /add.")

    return DATE


def load_assignment_to_database(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']

    if len(update.message.photo) == 0:
        is_photo = False
        message = update.message.text.split("/add")[1].strip()
    else:
        is_photo = True
        file_id = update.message.photo[-1]['file_id']

    field = context.user_data['user_field_choice']
    date = context.user_data['seminar_date']

    if is_photo:
        write_data(user_id, file_id, field, date)

        update.message.reply_text(f'Фотография "{field}" успешно загружена!',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))
    else:
        write_data(user_id, message, field, date)

        update.message.reply_text(f"Задание по '{field}' на {date} успешно загружено!",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))

    update.message.bot.delete_message(context.user_data['command_to_add_chat_id'],
                                      context.user_data['command_to_add_mes_id_1'])

    return ConversationHandler.END


conv_handler_add_assignment_by_hand = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex('^Добавить задание вручную$'), add_assignment)],
    states={
        FIELD: [CallbackQueryHandler(choose_time_type_of_assignment)],
        TIME_TYPE: [CallbackQueryHandler(choose_assignment_date)],

        DATE: [CallbackQueryHandler(process_seminar_date),
               MessageHandler(Filters.photo & Filters.caption('^/add$'), load_assignment_to_database),
               CommandHandler("add", load_assignment_to_database)
               ]
    },
    fallbacks=[CommandHandler('start', start)],
)
