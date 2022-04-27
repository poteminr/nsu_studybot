from scripts.schedule_api import get_group_seminars
from scripts.bot_functions import generate_dates_of_future_seminars, get_current_seminar, convert_utc_to_local_time
from scripts.registration import start
from scripts.database import read_data
from scripts.assignment import Assignment
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить/Редактировать задание вручную']]
reply_markup_keyboard = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

FIELD, TIME_TYPE, DATE = range(3)
PICK_DATE, CHOOSE_ANOTHER_DATE = range(2)


def add_during_seminar(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_data = read_data(user_id)
    user_group = user_data['group']
    user_utc_delta = user_data['utc_delta']

    date = convert_utc_to_local_time(update.message.date, user_utc_delta)

    if user_group is not None:
        seminar_name, seminar_weekdays = get_current_seminar(user_group, date)

        if seminar_name is not None:
            future_seminars_dates = generate_dates_of_future_seminars(date, seminar_weekdays)
            next_seminar_date = future_seminars_dates[0]

            assignment = Assignment(seminar_name=seminar_name, date=next_seminar_date,
                                    future_seminars_dates=future_seminars_dates)

            assignment.parse_message(update.message)

            context.user_data['assignment'] = assignment

            keyboard = [
                [InlineKeyboardButton(f"Добавить '{seminar_name}' на следующий семинар ({next_seminar_date})",
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


def choose_another_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_choice = query.data
    user_id = query.message.chat.id
    assignment = context.user_data['assignment']

    if user_choice == 'next_seminar':
        assignment.upload_to_database(user_id)
        query.edit_message_text(assignment.get_text_for_reply())

        return ConversationHandler.END

    elif user_choice == 'other_dates':
        buttons = [InlineKeyboardButton(date, callback_data=date) for date in assignment.future_seminars_dates]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Выберите дату занятия.", reply_markup=reply_markup)

        return CHOOSE_ANOTHER_DATE


def upload_to_another_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    assignment = context.user_data['assignment']
    assignment.date = query.data

    user_id = query.message.chat.id

    assignment.upload_to_database(user_id)
    query.edit_message_text(assignment.get_text_for_reply())

    return ConversationHandler.END


conv_handler_add_assignment_during_seminar = ConversationHandler(
    entry_points=[MessageHandler(Filters.photo & Filters.caption_regex(r'/add'), add_during_seminar),
                  CommandHandler("add", add_during_seminar)],
    states={
        PICK_DATE: [CallbackQueryHandler(choose_another_date)],
        CHOOSE_ANOTHER_DATE: [CallbackQueryHandler(upload_to_another_date)]

    },
    fallbacks=[CommandHandler('start', start)],
)


def add_assignment(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']
    context.user_data['user_group'] = user_group

    if user_group is not None:
        context.user_data['command_to_add_mes_id_1'] = update.message['message_id']

        seminars, _, seminars_weekdays = get_group_seminars(user_group)

        context.user_data['seminars_weekdays'] = seminars_weekdays

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(ind))] for ind, seminar_name in
                    enumerate(seminars)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(f'Выберите необходимый предмет', reply_markup=reply_markup)

        return FIELD

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=reply_markup_keyboard)


def choose_assignment_time_type(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    seminar_index = query.data
    seminar_name = query.message.reply_markup.inline_keyboard[int(seminar_index)][0]['text']

    assignment = Assignment(seminar_name=seminar_name)
    context.user_data['assignment'] = assignment

    keyboard = [
        [InlineKeyboardButton("Добавить задание на будущие занятия", callback_data='future_seminars')],
        [InlineKeyboardButton("Редактировать добавленные задания", callback_data='past_seminars')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Выберите дату занятия", reply_markup=reply_markup)

    return TIME_TYPE


def choose_assignment_date(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat['id']
    user_data = read_data(user_id)
    user_utc_delta = user_data['utc_delta']

    date = convert_utc_to_local_time(query.message.date, user_utc_delta)

    assignment = context.user_data['assignment']

    assignment_time_type = query.data
    context.user_data['assignment_time_type'] = assignment_time_type

    seminar_weekdays = context.user_data['seminars_weekdays'][assignment.seminar_name]

    keyboard = None
    if assignment_time_type == "future_seminars":
        assignment.future_seminars_dates = generate_dates_of_future_seminars(date, seminar_weekdays)

        buttons = [InlineKeyboardButton(date, callback_data=date) for date in assignment.future_seminars_dates]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

    elif assignment_time_type == "past_seminars":
        if assignment.seminar_name not in user_data.keys():
            query.edit_message_text(f'Нет добавленных заданий по "{assignment.seminar_name}"')
            return ConversationHandler.END

        dates_of_added_assignments = list(user_data[assignment.seminar_name].keys())

        buttons = [InlineKeyboardButton(date, callback_data=date) for date in dates_of_added_assignments]
        keyboard = [buttons[k:k + 2] for k in range(0, len(buttons), 2)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите дату занятия.", reply_markup=reply_markup)

    return DATE


def process_assignment_date(update: Update, context: CallbackContext):
    query = update.callback_query

    query.answer()
    assignment = context.user_data['assignment']
    assignment.date = query.data

    if context.user_data['assignment_time_type'] == 'future_seminars':
        bot_reply_message = query.edit_message_text(text=f"Отправьте фотографию или текст!\n1) Используйте /add как подпись к фотографии "
                                     f"\n2) /add текст")

    else:
        user_id = query.message.chat['id']
        user_data = read_data(user_id)

        data = user_data[assignment.seminar_name][assignment.date]

        if 'photo' in data.keys():
            if 'text' in data.keys():
                bot_reply_message = update.callback_query.message.reply_photo(data['photo'], caption=f"'{assignment.seminar_name}' на {assignment.date}"
                                                                                 f"\n\nТекст: {data['text']}"
                                                                                 f"\n\nОтправьте фотографию или текст, чтобы заменить задание!"
                                                                                 f"\n1) Используйте /add как подпись к фотографии "
                                                                                 f"\n2) /add текст")
            else:
                bot_reply_message = update.callback_query.message.reply_photo(data['photo'], caption=f"'{assignment.seminar_name}' на {assignment.date}"
                                                                                 f"\n\nОтправьте фотографию или текст, чтобы заменить задание!"
                                                                                 f"\n1) Используйте /add как подпись к фотографии "
                                                                                 f"\n2) /add текст")

            query.delete_message()

        else:
            bot_reply_message = query.edit_message_text(text=f"{assignment.seminar_name} на {assignment.date}:"
                                                             f"\n{data['text']} " 
                                                             f"\n\nОтправьте фотографию или текст, чтобы заменить задание!"
                                                             f"\n1) Используйте /add как подпись к фотографии "
                                                             f"\n2) /add текст")

    context.user_data['bot_reply_message_id'] = bot_reply_message['message_id']

    return DATE


def upload_assignment_to_database(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    assignment = context.user_data['assignment']

    assignment.parse_message(update.message)
    assignment.upload_to_database(user_id)

    update.message.reply_text(assignment.get_text_for_reply(), reply_markup=reply_markup_keyboard)

    update.message.bot.delete_message(update.message.chat['id'],
                                      context.user_data['command_to_add_mes_id_1'])

    update.message.bot.delete_message(update.message.chat['id'],
                                      context.user_data['bot_reply_message_id'])

    return ConversationHandler.END


conv_handler_add_assignment_by_hand = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex('^Добавить/Редактировать задание вручную$'), add_assignment)],
    states={
        FIELD: [CallbackQueryHandler(choose_assignment_time_type)],
        TIME_TYPE: [CallbackQueryHandler(choose_assignment_date)],

        DATE: [CallbackQueryHandler(process_assignment_date),
               MessageHandler(Filters.photo & Filters.caption_regex(r'/add'), upload_assignment_to_database),
               CommandHandler("add", upload_assignment_to_database)
               ]
    },
    fallbacks=[CommandHandler('start', start)],
)
