from scripts.database import read_data
from scripts.schedule_api import get_group_seminars
from scripts.registration import start
import datetime
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    MessageHandler, Filters,
    ConversationHandler,
    CallbackQueryHandler
)

DATE, ASSIGNMENT = range(2)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить/Редактировать задание вручную']]


def view_assignment(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']

    if user_group is not None:
        context.user_data['command_to_view_message_id'] = update.message['message_id']

        seminars, _, _ = get_group_seminars(user_group)

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(ind))] for ind, seminar_name in
                    enumerate(seminars)]

        update.message.reply_text("Выберите необходимый предмет", reply_markup=InlineKeyboardMarkup(keyboard))

        return DATE
    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                   resize_keyboard=True))
        return ConversationHandler.END


def pick_seminar_date_from_list(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat.id
    user_data = read_data(user_id)

    field_index = query.data
    seminar_name = query.message.reply_markup.inline_keyboard[int(field_index)][0]['text']
    context.user_data['user_seminar_choice'] = seminar_name

    if seminar_name not in user_data.keys():
        query.edit_message_text(text=f'Данные по предмету "{seminar_name}" отсутствуют')

        return ConversationHandler.END

    else:
        seminar_dates_with_assignments = list(user_data[seminar_name].keys())
        seminar_dates_with_assignments.sort(key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))

        keyboard = [[InlineKeyboardButton(date, callback_data=date)] for date in seminar_dates_with_assignments]

        query.edit_message_text(text="Выберите дату занятия.", reply_markup=InlineKeyboardMarkup(keyboard))

        return ASSIGNMENT


def send_assignment_to_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.message.chat.id

    user_data = read_data(user_id)

    seminar_date = query.data
    seminar_name = context.user_data['user_seminar_choice']

    if seminar_name in user_data.keys():
        data = user_data[seminar_name][seminar_date]
        if 'photo' in data.keys():
            if 'text' in data.keys():
                update.callback_query.message.reply_photo(data['photo'], caption=f"'{seminar_name}' на {seminar_date}"
                                                                                 f"\n\nТекст: {data['text']}")
            else:
                update.callback_query.message.reply_photo(data['photo'], caption=f"'{seminar_name}' на {seminar_date}")

            query.delete_message()

        else:
            query.edit_message_text(text=f"{seminar_name} на {seminar_date}:\n{data['text']}")

    else:
        query.edit_message_text(text=f'Данные по предмету "{seminar_name}" отсутствуют')

    update.callback_query.message.bot.delete_message(query.message.chat.id,
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
