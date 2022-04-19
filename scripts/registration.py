from scripts.bot_functions import university_codes2city, university_codes2text, get_utc_delta_by_city
from scripts.database import write_data
from scripts.schedule_api import get_group_id
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

FIRST_STAGE, SECOND_STAGE = range(2)

reply_keyboard = [['Просмотреть домашние задания'], ['Добавить задание вручную']]


def start(update: Update, _: CallbackContext):
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    update.message.reply_photo(photo=open("images/studybot_info.png", 'rb'), reply_markup=ReplyKeyboardRemove())

    keyboard = [
        [InlineKeyboardButton("Новосибирск", callback_data=str(1))],

        [InlineKeyboardButton("Москва", callback_data=str(2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите свой город 🏢", reply_markup=reply_markup)

    return FIRST_STAGE


def start_over(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("Новосибирск", callback_data=str(1))],
        [InlineKeyboardButton("Москва", callback_data=str(2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой город 🏢", reply_markup=reply_markup)

    return FIRST_STAGE


def choose_university_nsk(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("НГУ", callback_data=str(1.1))],
        [InlineKeyboardButton("НГТУ", callback_data=str(1.2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой университет 🧑🏻‍🎓", reply_markup=reply_markup)

    return FIRST_STAGE


def choose_university_msk(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("МГУ", callback_data=str(2.1))],
        [InlineKeyboardButton("МГТУ", callback_data=str(2.2))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Выберите свой университет 🧑🏻‍🎓", reply_markup=reply_markup)

    return FIRST_STAGE


def confirm_choice_of_university(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.message.chat.id
    user_university_code = query.data
    user_city = university_codes2city(query.data)

    write_data(user_id, user_university_code, 'university_code')
    write_data(user_id, user_city, 'city')
    write_data(user_id, get_utc_delta_by_city(user_city), 'utc_delta')

    keyboard = [
        [
            InlineKeyboardButton("Выбрать еще раз", callback_data=str(1)),
            InlineKeyboardButton("Подтвердить", callback_data=str(2)),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=f"Вы выбрали {university_codes2text(query.data)}. Всё верно?",
                            reply_markup=reply_markup)

    return SECOND_STAGE


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
        write_data(user_id, user_group, 'group')

        text = f"Группа {user_group}, отлично! Чтобы сменить, используйте команду заново."
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False,
                                                                         resize_keyboard=True))
    except KeyError:
        write_data(user_id, None, 'group')
        update.message.reply_text(f"Группа {user_group} не найдена, используйте команду еще раз.", )


conv_handler_pick_university = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        FIRST_STAGE: [
            CallbackQueryHandler(choose_university_nsk, pattern='^' + str(1) + '$'),
            CallbackQueryHandler(choose_university_msk, pattern='^' + str(2) + '$'),
            CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(1.1) + '$'),
            CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(1.2) + '$'),
            CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(2.1) + '$'),
            CallbackQueryHandler(confirm_choice_of_university, pattern='^' + str(2.2) + '$'),
        ],
        SECOND_STAGE: [
            CallbackQueryHandler(start_over, pattern='^' + str(1) + '$'),
            CallbackQueryHandler(university_selection_end, pattern='^' + str(2) + '$'),
        ],
    },
    fallbacks=[CommandHandler('start', start)],
)
