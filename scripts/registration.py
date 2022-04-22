from scripts.bot_functions import university_code2text
from scripts.database import write_data, read_cities_data
from scripts.schedule_api import get_group_id
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

CITY, UNIVERSITY, CONFIRMATION = range(3)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]


def start(update: Update, _: CallbackContext):
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    update.message.reply_photo(photo=open("images/studybot_info.png", 'rb'), reply_markup=ReplyKeyboardRemove())

    cities_data = read_cities_data()

    keyboard = [[InlineKeyboardButton(cities_data[city_code]['name'], callback_data=city_code)] for city_code in
                cities_data]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите свой город 🏢", reply_markup=reply_markup)

    return CITY


def start_over(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    cities_data = read_cities_data()
    keyboard = [[InlineKeyboardButton(cities_data[city_code]['name'], callback_data=city_code)] for city_code in
                cities_data]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой город 🏢", reply_markup=reply_markup)

    return CITY


def choose_university(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    city_code = query.data
    city_data = read_cities_data()[city_code]
    universities = city_data['universities_codes']

    context.user_data['utc_delta'] = city_data['utc_delta']
    context.user_data['city_name'] = city_data['name']

    keyboard = [[InlineKeyboardButton(universities[university_code], callback_data=university_code)] for university_code
                in universities]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой университет 🧑🏻‍🎓", reply_markup=reply_markup)

    return UNIVERSITY


def confirm_choice_of_university(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat.id
    user_university_code = query.data

    city_name = context.user_data['city_name']
    utc_delta = context.user_data['utc_delta']

    write_data(user_id, 'university_code', user_university_code)
    write_data(user_id, 'city', city_name)
    write_data(user_id, 'utc_delta', utc_delta)

    keyboard = [
        [
            InlineKeyboardButton("Выбрать еще раз", callback_data=str(1)),
            InlineKeyboardButton("Подтвердить", callback_data=str(2)),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Вы выбрали {university_code2text(query.data)}. Всё верно?",
                            reply_markup=reply_markup)

    return CONFIRMATION


def university_selection_end(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    query.edit_message_text(text="Университет выбран! \nТеперь используйте '/group номер группы'")

    return ConversationHandler.END


def init_user_group(update: Update, _: CallbackContext):
    user = update.message.from_user
    user_id = update.message.chat['id']
    user_group = int(update.message.text.split(" ")[1])

    logger.info("Group of %s: %s", user.first_name, user_group)

    try:
        get_group_id(user_group)
        write_data(user_id, 'group', user_group)

        text = f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново."
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                         resize_keyboard=True))
    except KeyError:
        write_data(user_id, 'group', None)
        update.message.reply_text(f"Группа {user_group} не найдена, используйте команду еще раз.", )


conv_handler_pick_university = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CITY: [
            CallbackQueryHandler(choose_university)
        ],

        UNIVERSITY: [
            CallbackQueryHandler(confirm_choice_of_university)
        ],
        CONFIRMATION: [
            CallbackQueryHandler(start_over, pattern='^' + str(1) + '$'),
            CallbackQueryHandler(university_selection_end, pattern='^' + str(2) + '$'),
        ],
    },
    fallbacks=[CommandHandler('start', start)],
)
