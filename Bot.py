import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Scrape import Menu
import json
import os
import datetime
from fuzzywuzzy import fuzz

# Log messages to the server to get insights about user activities beside the print statements
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Log data to file FoodBot.log
logger = logging.getLogger(__name__)
fh = logging.FileHandler('CrispyBeefAlert.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

TOKEN = 0

PATH = 0

MENSA = ("Clausiusbar" ,"Dozentenfoyer" ,"food&lab" ,"Foodtrailer" ,"G-ESSbar" ,"Polyterrasse" ,"Polysnack" ,"Tannenbar")

ETHmensa = {"Clausiusbar": 4, "Dozentenfoyer": 6, "food&lab": 28, "Foodtrailer": 9, "G-ESSbar": 11,
            "Polyterrasse": 12, "Polysnack": 13, "Tannenbar": 14, "Mercato UZH Zentrum": "zentrum-mercato",
            "Mercato UZH Zentrum Abend": "zentrum-mercato-abend",
            "Mensa UZH Zentrum": "zentrum-mensa", "Mensa UZH Zentrum Lichthof Rondell": "lichthof-rondell",
            "Mensa UZH Irchel": "mensa-uzh-irchel", "Cafeteria UZH Irchel Atrium": "irchel-cafeteria-atrium",
            "Cafeteria UZH Irchel Seerose": "irchel-cafeteria-seerose-mittag",
            "Cafeteria UZH Irchel Seerose": "irchel-cafeteria-seerose-abend",
            "Mensa UZH Binzmühle": "mensa-uzh-binzmuehle", "Cafeteria UZH Cityport": "mensa-uzh-cityport",
            "Rämi 59": "raemi59", "Cafeteria Zentrum für Zahnmedizin (ZZM)": "cafeteria-zzm",
            "Cafeteria UZH Tierspital": "cafeteria-uzh-tierspital",
            "Cafeteria UZH Botanischer Garten": "cafeteria-uzh-botgarten",
            "Cafeteria UZH Plattenstrasse": "cafeteria-uzh-plattenstrasse"}

# function that is executed when the user types /start
def start(bot, update):
    # Sending some welcome messages and instructions about the bot usage
    print(update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Einleitung',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# function that is executed when the user types /help
def help(bot, update):
    # send back  help instructions
    bot.send_message(chat_id=update.message.chat_id,
                     text='Help',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# function reads the users messages
def listen(bot, update):
    response = update.message.text
    mensa, menu = 0, 0

    #Check if command present
    if "<save>" in response:
        print("New save request")
        # search for known mensa name
        for word in [*ETHmensa]:
            print(word)
            print(fuzz.token_set_ratio(word, response))
            if fuzz.token_set_ratio(word, response) > 50:
                mensa = ETHmensa[word]
                print(mensa)

                # search for menu name which should be between two "
                menu = response.split('"')[1]
                # local path concatenate with relative path of json
                my_path = os.path.abspath(os.path.dirname(__file__))
                newpath = os.path.join(my_path, PATH)
                # read in json
                with open(newpath) as f:
                    data = json.load(f)

                # check json for key of mensa, if not present create empty one
                if mensa not in data:
                    data[mensa]={}

                # check json for menu for that mensa, if not create empty list
                if menu not in data[mensa]:
                    data[mensa][menu]=[]

                # add chat id to that mensa-menu combination
                data[mensa][menu].append(update.message.chat_id)
                # update last edited key of json
                data["lastUpdate"] = str(datetime.datetime.now())
                #save updated json
                with open(PATH, 'w') as jsonFile:
                    json.dump(data, jsonFile)



    bot.send_message(chat_id=update.message.chat_id,
                     text='I have no news for you. I will message you as soon as I know more',
                     parse_mode=telegram.ParseMode.MARKDOWN)


# function that is being executed when an error occurs
def error(bot, update, error):
    # Logg all errors as warnings as well as the current update to analyse it later on
    logger.warning('Update "%s" caused error "%s"', update, error)

# Reacting to unknown commands via printing help
def unknown(bot, update):
    help(bot, update)


def sendMessage(msg, chat_id, token=TOKEN):
	"""
	Send a mensage to a telegram user specified on chatId
	chat_id must be a number!
	"""
	bot = telegram.Bot(token=token)
	bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


def main():
    # Read my personal bot token out of the token.txt file which is not uploaded to github, and hand it to the updater.
    print("Starting Bot")
    config = open("config.txt", "r")
    for line in config:
        if line.startswith("TOKEN"):
            token = line.split("TOKEN: ")[1].rstrip()
        if line.startswith("JSONPATH:"):
            path = line.split("JSONPATH: ")[1].rstrip()
    global TOKEN
    TOKEN = str(token)
    global PATH
    PATH = path
    print(PATH)
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Tell dispatcher which functions are to execute according to which user commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("hilfe", help))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Handler that listens to user messages as text and reacts to it
    dispatcher.add_handler(MessageHandler(Filters.text, listen))

    # Error handling that calls the error function to log the error messages
    dispatcher.add_error_handler(error)

    # Start bot
    updater.start_polling()

    # Keep the bot alive even though nobody is requesting anything
    updater.idle()


if __name__ == '__main__':
    main()