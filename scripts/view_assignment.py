from scripts.database import read_data
from scripts.schedule_api import get_group_seminars
from scripts.registration import start
from scripts.assignment import Assignment
import datetime
from telegram_bot_pagination import InlineKeyboardSimplePaginator
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    MessageHandler, Filters,
    ConversationHandler,
    CallbackQueryHandler
)

DATE, ASSIGNMENT = range(2)

reply_keyboard = [['Просмотреть домашние задания'],
                  ['Добавить/Редактировать задание вручную']]


def view_assignment(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']

    if user_group is not None:
        context.user_data['command_to_view_message_id'] = update.message['message_id']

        seminars, _, _ = get_group_seminars(user_group)

        keyboard = [[InlineKeyboardButton(seminar_name, callback_data=str(seminar_index))]
                    for seminar_index, seminar_name in enumerate(seminars)]

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
    user_assignments = read_data(user_id)['assignments']

    seminar_index = query.data
    seminar_name = query.message.reply_markup.inline_keyboard[int(seminar_index)][0]['text']
    context.user_data['user_seminar_choice'] = seminar_name

    if seminar_name not in user_assignments.keys():
        query.edit_message_text(text=f'Данные по предмету "{seminar_name}" отсутствуют')

        update.callback_query.message.bot.delete_message(user_id,
                                                         context.user_data['command_to_view_message_id'])

        return ConversationHandler.END

    else:
        seminar_dates_with_assignments = list(user_assignments[seminar_name].keys())
        seminar_dates_with_assignments.sort(key=lambda d: datetime.datetime.strptime(d, "%d.%m.%Y"))

        keyboard = [[InlineKeyboardButton(date, callback_data=date)] for date in seminar_dates_with_assignments]

        query.edit_message_text(text="Выберите дату занятия.", reply_markup=InlineKeyboardMarkup(keyboard))

        return ASSIGNMENT


def send_assignment_to_user(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat.id
    user_assignments = read_data(user_id)['assignments']

    seminar_date = query.data
    seminar_name = context.user_data['user_seminar_choice']

    if seminar_name in user_assignments.keys():
        seminar_data = user_assignments[seminar_name][seminar_date]
        if 'photo_data' in seminar_data.keys():
            if 'text_data' in seminar_data.keys():
                update.callback_query.message.reply_photo(seminar_data['photo_data'], caption=f"'{seminar_name}' на {seminar_date}"
                                                                                 f"\n\nТекст: {seminar_data['text_data']}")
            else:
                update.callback_query.message.reply_photo(seminar_data['photo_data'], caption=f"'{seminar_name}' на {seminar_date}")

            query.delete_message()

        else:
            query.edit_message_text(text=f"{seminar_name} на {seminar_date}:\n{seminar_data['text_data']}")

    else:
        query.edit_message_text(text=f'Данные по предмету "{seminar_name}" отсутствуют')

    update.callback_query.message.bot.delete_message(user_id,
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


def view_assignment_for_specific_date(update: Update, context: CallbackContext):
    user_id = update.message.chat['id']
    message = update.message.text

    date = message.split('/view')[1].strip()
    user_assignments = read_data(user_id)['assignments']

    # delete the previous message with pages if the user used /view again
    if 'assignment_for_specific_date_id' in context.user_data.keys():
        update.message.bot.delete_message(user_id, context.user_data['assignment_for_specific_date_id'])

    assignments_for_the_date = []
    for seminar_name in user_assignments.keys():
        if date in user_assignments[seminar_name].keys():
            assignment = Assignment(seminar_name=seminar_name, date=date, **user_assignments[seminar_name][date])
            assignments_for_the_date.append(assignment.create_text())

    if len(assignments_for_the_date) != 0:
        paginator = InlineKeyboardSimplePaginator(
            page_count=len(assignments_for_the_date),
            data_pattern='assignment#{page}'
        )

        assignments_for_specific_date_message = update.message.reply_text(
            text=assignments_for_the_date[0],
            reply_markup=paginator.markup,
            parse_mode='Markdown'
        )

        context.user_data['assignments_for_the_date'] = assignments_for_the_date
        context.user_data['assignment_for_specific_date_id'] = assignments_for_specific_date_message.message_id
    else:
        update.message.reply_text(f'Заданий на {date} не найдено!')

    update.message.bot.delete_message(user_id, update.message.message_id)


def view_page(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    assignments_for_the_date = context.user_data['assignments_for_the_date']

    page = int(query.data.split('#')[1])

    paginator = InlineKeyboardSimplePaginator(
        len(assignments_for_the_date),
        current_page=page,
        data_pattern='assignment#{page}'
    )

    query.edit_message_text(
        text=assignments_for_the_date[page - 1],
        reply_markup=paginator.markup,
        parse_mode='Markdown'
    )
