import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Scrape import Menu

# Log messages to the server to get insights about user activities beside the print statements
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Log data to file FoodBot.log
logger = logging.getLogger(__name__)
fh = logging.FileHandler('CrispyBeefAlert.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# function that is executed when the user types /start
def start(alertBot, update):
    # Sending some welcome messages and instructions about the bot usage
    print(update.message.chat_id)
    alertBot.send_message(chat_id=update.message.chat_id,
                     text='Einleitung',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# function that is executed when the user types /help
def help(alertBot, update):
    # send back  help instructions
    alertBot.send_message(chat_id=update.message.chat_id,
                     text='Help',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# function reads the users messages
def mensa(alertBot, update):
    response = update.message.text
    alertBot.send_message(chat_id=update.message.chat_id,
                     text='I have no news for you. I will message you as soon as I know more',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# function that is being executed when an error occurs
def error(alertBot, update, error):
    # Logg all errors as warnings as well as the current update to analyse it later on
    logger.warning('Update "%s" caused error "%s"', update, error)

# Reacting to unknown commands via printing help
def unknown(alertBot, update):
    help(alertBot, update)


def main():
    # Read my personal bot token out of the token.txt file which is not uploaded to github, and hand it to the updater.
    print("Starting Bot")
    token = open("token.txt", "r").read()
    updater = Updater(token)
    dispatcher = updater.dispatcher

    # Tell dispatcher which functions are to execute according to which user commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("hilfe", help))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Handler that listens to user messages as text and reacts to it
    dispatcher.add_handler(MessageHandler(Filters.text, mensa))

    # Error handling that calls the error function to log the error messages
    dispatcher.add_error_handler(error)

    # Start bot
    updater.start_polling()

    # Keep the bot alive even though nobody is requesting anything
    updater.idle()


if __name__ == '__main__':
    main()