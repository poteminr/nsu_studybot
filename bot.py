import json
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext,MessageHandler, Filters, ConversationHandler
from bot_functions import write_data, get_schedule, read_data


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

reply_keyboard = [['Смотреть']]
SUBJECT = range(1)


def start(update: Update, _: CallbackContext):
    text_part_one = "Привет, это StudyBot, отправляй изображение домашней работы и мы составим личное расписние!\n"
    text_part_two =  "Введите номер группы '/group номер', чтобы начать работу!\n"
    
    update.message.reply_text(text_part_one + text_part_two, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))


def group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = user['id']
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)
    
    write_data(user_id, 'group', user_group)

    update.message.reply_text(f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново!")


def add(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = user['id']
    date = update.message.date
    

    file_id = update.message.photo[-1]['file_id']
 
    logger.info("Photo of %s: %s", user.first_name, file_id)
    field = get_schedule(user_id, date)    


    write_data(user_id, field, file_id)

    update.message.reply_text(f'Фотография "{field}" успешно загружена!')


def view(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user['id']
    text = update.message.text
    context.user_data['choice'] = text

    update.message.reply_text(f'Введите номер необходимого предмета.')
    
    subjects = list(read_data(user_id).keys())[1:]

    for index, field in enumerate(subjects):
        update.message.reply_text(f'{index+1}. {field}')

    return SUBJECT


def show(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = user['id']
    user_data = read_data(user_id)

    number = int(update.message.text)
    
    field = list(user_data.keys())[1:][number-1]

    file_id = user_data[field]

    update.message.reply_photo(file_id)
    
    return ConversationHandler.END



def delete(update: Update, _: CallbackContext):
    raise NotImplementedError


def cancel(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Пока', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    with open('keys.json') as f:
        keys = json.load(f)

    updater = Updater(token=keys['token'], use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("group", group))
    dispatcher.add_handler(CommandHandler("delete", delete))
    dispatcher.add_handler(MessageHandler(Filters.photo, add))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Смотреть$'), view)],
        states={
            SUBJECT: [MessageHandler(Filters.regex('^[-+]?([1-9]\d*|0)$'), show)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
            )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()