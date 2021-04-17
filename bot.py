import json
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext,MessageHandler, Filters, ConversationHandler
from bot_functions import write_data, read_data, get_seminar_number_by_time
from schedule_api import get_group_seminars, get_time_by_id


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]

SUBJECT = range(1)


def start(update: Update, _: CallbackContext):
    text_part_one = "Привет, это StudyBot, отправляй изображение домашней работы и мы составим личное расписние!\n"
    text_part_two =  "Введите номер группы '/group номер', чтобы начать работу!\n"
    text_part_three = "Для использованиях в чате группы добавляйте /add как подпись к фото!\n"
    update.message.reply_text(text_part_one + text_part_two + text_part_three, 
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))


def group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)
    
    write_data(user_id, 'group', user_group)

    update.message.reply_text(f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново!")


def add(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    date = update.message.date
    file_id = update.message.photo[-1]['file_id']
 
    logger.info("Photo of %s: %s", user.first_name, file_id)
    field = get_seminar_number_by_time(user_id, date)    

    if field != None:
        write_data(user_id, field, file_id)

        update.message.reply_text(f'Фотография "{field}" успешно загружена!', 
                                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))
    else:
        update.message.reply_text(f'Занятия сейчас нет. Попробуйте добавить фото вручную!', 
                                    reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))


def view(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']

    subjects, _ = get_group_seminars(user_group)
    value = len(subjects)
    
    part_one = subjects[:int(value / 3)]
    part_two = subjects[int(value / 3):int(value / 3) * 2]
    part_three = subjects[int(value / 3) * 2:]

    keyboard = [part_one, part_two, part_three]

    update.message.reply_text(f'Выберите необходимый предмет.', 
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))

    return SUBJECT


def show(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_data = read_data(user_id)

    field = update.message.text
    
    if field in user_data.keys():

        file_id = user_data[field]

        # next_lesson_date = get_next_lesson_date(user_id, field)

        update.message.reply_photo(file_id, reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(f'Удачи!', 
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        
        return ConversationHandler.END
    else:
        update.message.reply_text(f'Данные отсутствуют.', 
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        
        return ConversationHandler.END


FIELD, ADDED = range(2)

def add_by_hand(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = read_data(user_id)['group']

    subjects, _ = get_group_seminars(user_group)
    value = len(subjects)
    
    part_one = subjects[:int(value / 3)]
    part_two = subjects[int(value / 3):int(value / 3) * 2]
    part_three = subjects[int(value / 3) * 2:]

    keyboard = [part_one, part_two, part_three]

    update.message.reply_text(f'Выберите необходимый предмет.', 
                              reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))

    return FIELD


def pick_field_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
 
    field = update.message.text
    context.user_data['choice'] = field
    update.message.reply_text(f'Отлично, теперь отправьте фотографию!')

    return ADDED


def load_by_hand(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    # date = update.message.date
    file_id = update.message.photo[-1]['file_id']
 
    logger.info("Photo of %s: %s", user.first_name, file_id)

    field = context.user_data['choice']
    
    write_data(user_id, field, file_id)

    update.message.reply_text(f'Фотография "{field}" успешно загружена!', 
                                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True))
    
    return ConversationHandler.END


def delete(update: Update, _: CallbackContext):
    raise NotImplementedError


def cancel(update: Update, _: CallbackContext):
    user = update.message.from_user
    
    logger.info("User %s canceled the conversation.", user.first_name)

    update.message.reply_text('Пока', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
    with open('keys.json') as f:
        keys = json.load(f)

    updater = Updater(token=keys['token'], use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("group", group))
    dispatcher.add_handler(CommandHandler("delete", delete))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Просмотреть домашние задания$'), view)],
        states={
            SUBJECT: [MessageHandler(Filters.text & ~(Filters.command), show)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
            )

    dispatcher.add_handler(conv_handler)

    conv_handler_two = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Добавить задание вручную$'), add_by_hand)],
        states={
            FIELD: [MessageHandler(Filters.text & ~(Filters.command), pick_field_by_hand)],
            ADDED: [MessageHandler(Filters.photo & ~(Filters.command), load_by_hand)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
            )

    dispatcher.add_handler(conv_handler_two)
    dispatcher.add_handler(MessageHandler(Filters.photo, add))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()