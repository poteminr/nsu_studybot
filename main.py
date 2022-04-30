from scripts.private_keys import import_private_keys
from scripts.registration import init_user_group, conv_handler_pick_university
from scripts.view_assignment import conv_handler_view_assignment, view_assignment_for_specific_date, view_page
from scripts.add_assignment import conv_handler_add_assignment_by_hand, conv_handler_add_assignment_during_seminar
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def restart(update: Update, _: CallbackContext):
    user = update.message.from_user

    logger.info("User %s canceled the conversation.", user.first_name)

    update.message.reply_text(text="Бот перезагружен!")

    return ConversationHandler.END


def main():
    API_KEY = import_private_keys(json_path='keys.json', key_name='token')

    updater = Updater(token=API_KEY, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("group", init_user_group))

    dispatcher.add_handler(conv_handler_pick_university)

    dispatcher.add_handler(conv_handler_view_assignment)

    dispatcher.add_handler(conv_handler_add_assignment_by_hand)

    dispatcher.add_handler(conv_handler_add_assignment_during_seminar)

    dispatcher.add_handler(CommandHandler("restart", restart))

    dispatcher.add_handler(CommandHandler("view", view_assignment_for_specific_date))
    updater.dispatcher.add_handler(CallbackQueryHandler(view_page, pattern='^assignment#'))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
