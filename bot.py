import json
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext
from bot_functions import write_data
import json
from bot_functions import write_data



# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


reply_keyboard = [
    ['Группа', 'Расписание'],
    ['Добавить', 'Удалить']
]


markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)


def start(update: Update, _: CallbackContext):
    text_part_one = "Привет, это StudyBot, отправляй изображение домашней работы и мы составим личное расписние!\n"
    text_part_two =  "Введите номер группы '/group номер', чтобы начать работу!\n"
    
    update.message.reply_text(text_part_one + text_part_two, reply_markup=markup)


def group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = user['id']
    print(user)
    
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)

    update.message.reply_text(f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново!")
    
    write_data(user_id, 'group', user_group)

def main():
    with open('keys.json') as f:
        keys = json.load(f)

    updater = Updater(token=keys['token'], use_context=True)


    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("group", group))
    # dispatcher.add_handler(CommandHandler("unset", unset))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()