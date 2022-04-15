from scripts.schedule_api import get_group_seminars
from scripts.bot_functions import read_data, generate_dates_of_future_seminars, write_data, get_seminar_info_by_time
from scripts.registration import start
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler

FIELD, TIME_TYPE, DATE = range(3)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]

PICK_DATE = range(1)


def add_during_seminar(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    date = update.message.date

    user_group = read_data(user_id)['group']
    reply_markup_keyboard = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

    if user_group is not None:
        if len(update.message.photo) == 0:
            is_photo = False
            data = update.message.text.split("/add")[1].strip()
        else:
            is_photo = True
            data = update.message.photo[-1]['file_id']

        field, seminar_weekdays = get_seminar_info_by_time(user_id, date)

        if field is not None:
            future_seminars_dates = generate_dates_of_future_seminars(date, seminar_weekdays)
            next_seminar_date = future_seminars_dates[0]

            context.user_data['homework_data'] = data
            context.user_data['is_photo'] = is_photo
            context.user_data['next_seminar_date'] = next_seminar_date
            context.user_data['field'] = field

            keyboard = [
                [InlineKeyboardButton(f"Добавить на следующий семинар ({next_seminar_date})",
                                      callback_data="next_seminar")],
                [InlineKeyboardButton("Записать на другую дату в будущем.", callback_data='other_dates')],
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
    field = context.user_data['field']

    if user_choice == 'next_seminar':
        is_photo = context.user_data['is_photo']
        data = context.user_data['homework_data']
        next_seminar_date = context.user_data['next_seminar_date']

        write_data(user_id, data, field, next_seminar_date)

        if is_photo:
            query.edit_message_text(f'Фотография "{field}" на {next_seminar_date} успешно загружена!')
        else:
            query.edit_message_text(f'Текст "{field}" на {next_seminar_date} успешно загружен!')

        return ConversationHandler.END
    elif user_choice == 'other_dates':
        raise NotImplemented


conv_handler_add_assignment_during_seminar = ConversationHandler(
    entry_points=[MessageHandler(Filters.photo & Filters.caption('^/add$'), add_during_seminar),
                  CommandHandler("add", add_during_seminar)],
    states={
        PICK_DATE: [CallbackQueryHandler(pick_other_dates)],

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
