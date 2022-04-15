from scripts.bot_functions import write_data, read_data, get_seminar_info_by_time
from scripts.private_keys import import_private_keys
from scripts.registration import init_user_group, conv_handler_pick_university
from scripts.view_assignment import conv_handler_view_assignment
from scripts.add_assignment import conv_handler_add_assignment_by_hand
import logging
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler, Filters,
    ConversationHandler
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUBJECT, B = range(2)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]


def restart(update: Update, _: CallbackContext):
    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.first_name)

    update.message.reply_text(text="Бот перезагружен!")

    return ConversationHandler.END


def add(update: Update, _: CallbackContext):
    user_id = update.message.chat['id']
    date = update.message.date

    user_group = read_data(user_id)['group']
    reply_markup_keyboard = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

    if user_group is not None:
        if len(update.message.photo) == 0:
            is_photo = False
            message = update.message.text.split("/add")[1].strip()
        else:
            is_photo = True
            file_id = update.message.photo[-1]['file_id']

        field, seminar_weekdays = get_seminar_info_by_time(user_id, date)

        if field is not None:
            # next_seminar_date = get_next_seminar_date(date, seminar_weekdays)
            # context.user_data['homework_data'] =

            if is_photo:
                write_data(user_id, field, file_id)

                update.message.reply_text(f'Фотография "{field}" успешно загружена!',
                                          reply_markup=reply_markup_keyboard)
            else:
                write_data(user_id, field, message)

                update.message.reply_text(f'Текст "{field}" успешно загружен!',
                                          reply_markup=reply_markup_keyboard)
        else:
            update.message.reply_text(f'Занятия сейчас нет. Попробуйте добавить вручную!',
                                      reply_markup=reply_markup_keyboard)

    else:
        update.message.reply_text(f'Необходимо ввести номер группы. (/group номер)',
                                  reply_markup=reply_markup_keyboard)


def main():
    API_KEY = import_private_keys(json_path='keys.json', key_name='token')

    updater = Updater(token=API_KEY, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("group", init_user_group))

    dispatcher.add_handler(conv_handler_pick_university)

    dispatcher.add_handler(conv_handler_view_assignment)

    dispatcher.add_handler(conv_handler_add_assignment_by_hand)
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.caption('^/add$'), add))
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("restart", restart))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
