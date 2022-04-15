from scripts.bot_functions import read_data
from scripts.schedule_api import get_group_seminars
from scripts.registration import start
import datetime
import telegram.error
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    MessageHandler, Filters,
    ConversationHandler,
    CallbackQueryHandler
)

DATE, ASSIGNMENT = range(2)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]


def view_assignment(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']

    if user_group is not None:

        context.user_data['command_to_view_message_id'] = update.message['message_id']
        context.user_data['command_to_view_chat_id'] = update.message.chat['id']

        subjects, _, _ = get_group_seminars(user_group)
        subjects = sorted(subjects)

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(ind))] for ind, seminar_name in
                    enumerate(subjects)]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text("Выберите необходимый предмет", reply_markup=reply_markup)

        return DATE

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))


def pick_seminar_date_from_list(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.message.chat.id

    user_data = read_data(user_id)

    field_index = query.data
    field_text = query.message.reply_markup.inline_keyboard[int(field_index)][0]['text']

    context.user_data['user_field_choice'] = field_text

    if field_text not in user_data.keys():
        query.edit_message_text(text=f'Данные по предмету: "{field_text}" отсутствуют.')

        return ConversationHandler.END

    seminar_dates_with_assignments = list(user_data[field_text].keys())
    seminar_dates_with_assignments.sort(key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))

    keyboard = [[InlineKeyboardButton(date, callback_data=date)] for date in seminar_dates_with_assignments]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите дату занятия.", reply_markup=reply_markup)

    return ASSIGNMENT


def send_assignment_to_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.message.chat.id

    user_data = read_data(user_id)

    field_date = query.data
    field_text = context.user_data['user_field_choice']

    if field_text in user_data.keys():
        data = user_data[field_text][field_date]
        try:
            update.callback_query.message.reply_photo(data, caption=f"{field_text}")
            query.delete_message()

        except telegram.error.BadRequest:
            query.edit_message_text(text=f"{field_text} на {field_date}: \n{data}")

    else:
        query.edit_message_text(text=f'Данные по предмету: "{field_text}" отсутствуют.')

    update.callback_query.message.bot.delete_message(context.user_data['command_to_view_chat_id'],
                                                     context.user_data['command_to_view_message_id'])

    return ConversationHandler.END


conv_handler_view_assignment = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Просмотреть домашние задания$'), view_assignment)],
        states={
            DATE: [CallbackQueryHandler(pick_seminar_date_from_list)],
            ASSIGNMENT: [CallbackQueryHandler(send_assignment_to_user)]
        },
        fallbacks=[CommandHandler('start', start)],
    )
