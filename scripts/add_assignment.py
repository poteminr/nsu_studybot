from scripts.schedule_api import get_group_seminars
from scripts.bot_functions import generate_dates_of_future_seminars, get_current_seminar, convert_utc_to_local_time
from scripts.registration import start
from scripts.database import read_data, write_assignment
from scripts.assignment import Assignment
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler

FIELD, TIME_TYPE, DATE = range(3)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]

PICK_DATE, CHOOSE_FROM_OTHER_DATE = range(2)


def add_during_seminar(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_data = read_data(user_id)
    user_group = user_data['group']
    user_utc_delta = user_data['utc_delta']

    date = convert_utc_to_local_time(update.message.date, user_utc_delta)

    reply_markup_keyboard = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

    if user_group is not None:
        if len(update.message.photo) == 0:
            assignment_type = 'text'
            data = update.message.text.split("/add")[1].strip()
        else:
            assignment_type = 'photo'
            data = update.message.photo[-1]['file_id']

        field, seminar_weekdays = get_current_seminar(user_group, date)

        if field is not None:
            future_seminars_dates = generate_dates_of_future_seminars(date, seminar_weekdays)
            next_seminar_date = future_seminars_dates[0]

            assignment = Assignment(seminar_name=field, date=next_seminar_date, assignment_type=assignment_type,
                                    data=data, future_seminars_dates=future_seminars_dates)

            context.user_data['assignment'] = assignment

            keyboard = [
                [InlineKeyboardButton(f"Добавить на следующий семинар ({next_seminar_date})",
                                      callback_data="next_seminar")],
                [InlineKeyboardButton("Выбрать другую дату", callback_data='other_dates')],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("На какой день записать?", reply_markup=reply_markup)

            return PICK_DATE

        else:
            update.message.reply_text(f'Занятия сейчас нет. Попробуйте добавить вручную!',
                                      reply_markup=reply_markup_keyboard)
    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=reply_markup_keyboard)


def pick_other_dates(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_choice = query.data
    user_id = query.message.chat.id
    assignment = context.user_data['assignment']

    if user_choice == 'next_seminar':
        write_assignment(user_id, assignment)
        query.edit_message_text(assignment.get_text_for_reply())

        return ConversationHandler.END

    elif user_choice == 'other_dates':
        buttons = [InlineKeyboardButton(date, callback_data=date) for date in assignment.future_seminars_dates]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Выберите дату занятия.", reply_markup=reply_markup)

        return CHOOSE_FROM_OTHER_DATE


def upload_to_other_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    assignment = context.user_data['assignment']
    assignment.date = query.data

    user_id = query.message.chat.id

    write_assignment(user_id, assignment)

    if assignment.assignment_type == 'photo':
        query.edit_message_text(f'Фотография "{assignment.seminar_name}" на {assignment.date} успешно загружена!')
    else:
        query.edit_message_text(f'Текст "{assignment.seminar_name}" на {assignment.date} успешно загружен!')

    return ConversationHandler.END


conv_handler_add_assignment_during_seminar = ConversationHandler(
    entry_points=[MessageHandler(Filters.photo & Filters.caption('^/add$'), add_during_seminar),
                  CommandHandler("add", add_during_seminar)],
    states={
        PICK_DATE: [CallbackQueryHandler(pick_other_dates)],
        CHOOSE_FROM_OTHER_DATE: [CallbackQueryHandler(upload_to_other_date)]

    },
    fallbacks=[CommandHandler('start', start)],
)


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

    assignment = Assignment(seminar_name=field_text)
    context.user_data['assignment'] = assignment

    keyboard = [
        [InlineKeyboardButton("Добавить задание на будущие занятия ", callback_data='future_seminars')],
        [InlineKeyboardButton("Редактировать добавленные задания", callback_data='past_seminars')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Выберите дату занятия.", reply_markup=reply_markup)

    return TIME_TYPE


def choose_assignment_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat['id']
    user_data = read_data(user_id)
    user_utc_delta = user_data['utc_delta']

    date = convert_utc_to_local_time(query.message.date, user_utc_delta)

    assignment = context.user_data['assignment']

    time_index = query.data

    seminar_weekdays = context.user_data['seminars_weekdays'][assignment.seminar_name]

    keyboard = None
    if time_index == "future_seminars":
        assignment.future_seminars_dates = generate_dates_of_future_seminars(date, seminar_weekdays)

        buttons = [InlineKeyboardButton(date, callback_data=date) for date in assignment.future_seminars_dates]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

    elif time_index == "past_seminars":
        if assignment.seminar_name not in user_data.keys():
            query.edit_message_text(f'Нет добавленных заданий по "{assignment.seminar_name}"')
            return ConversationHandler.END

        added_dates = list(user_data[assignment.seminar_name].keys())

        buttons = [InlineKeyboardButton(date, callback_data=date) for date in added_dates]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите дату занятия.", reply_markup=reply_markup)

    return DATE


def process_seminar_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    assignment = context.user_data['assignment']

    assignment.date = query.data

    query.edit_message_text(text=f"Отправьте фотографию или текст! Не забудьте добавить /add.")

    return DATE


def load_assignment_to_database(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    assignment = context.user_data['assignment']

    if len(update.message.photo) == 0:
        assignment.assignment_type = 'text'
        assignment.data = update.message.text.split("/add")[1].strip()
    else:
        assignment.assignment_type = 'photo'
        assignment.data = update.message.photo[-1]['file_id']

    write_assignment(user_id, assignment)

    update.message.reply_text(assignment.get_text_for_reply(),
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
