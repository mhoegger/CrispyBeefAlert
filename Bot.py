import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Scrape import Menu
import json
import os
import datetime
from fuzzywuzzy import fuzz


class MenuAlertBot:
    def __init__(self):
        self.TOKEN = None
        self.JSONPATH = None
        self.MENSA = {"Clausiusbar": 4, "Dozentenfoyer": 6, "food&lab": 28, "Foodtrailer": 9, "G-ESSbar": 11,
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
        self.MENSA_ALIAS = {
            "Clausiusbar": ["Clausiusbar", "AsiaMensa", "Clausius"],
            "Dozentenfoyer": ["Dozentenfoyer"],
            "food&lab": ["food&lab"],
            "Foodtrailer": ["Foodtrailer", "Imbissstand"],
            "G-ESSbar": ["G-ESSbar", "GESS"],
            "Polyterrasse": ["Polyterrasse", "Poly", "ETHMensa"],
            "Polysnack": ["Polysnack"],
            "Tannenbar": ["Tannenbar"],
            "Mercato UZH Zentrum": ["Mercato UZH Zentrum", "Untere Mensa", "Uni Mensa"],
            "Mercato UZH Zentrum Abend": ["Mercato UZH Zentrum Abend", "Uni Mensa Abend"],
            "Mensa UZH Zentrum": ["Mensa UZH Zentrum", "Obere Mensa"],
            "Mensa UZH Zentrum Lichthof Rondell": ["Mensa UZH Zentrum Lichthof Rondell", "Liechthof", "Rondell"],
            "Mensa UZH Irchel": ["Mensa UZH Irchel", "Irchel"],
            "Cafeteria UZH Irchel Atrium": ["Cafeteria UZH Irchel Atrium", "Atrium"],
            "Cafeteria UZH Irchel Seerose": ["Cafeteria UZH Irchel Seerose", "Seerose"],
            "Mensa UZH Binzmühle": ["Mensa UZH Binzmühle", "Binz"],
            "Cafeteria UZH Cityport": ["Cafeteria UZH Cityport", "Cityport"],
            "Rämi 59": ["Rämi 59", "rämi"],
            "Cafeteria Zentrum für Zahnmedizin (ZZM)": ["Cafeteria Zentrum für Zahnmedizin (ZZM)", "ZZM"],
            "Cafeteria UZH Tierspital": ["Cafeteria UZH Tierspital", "Tierspital"],
            "Cafeteria UZH Botanischer Garten": ["Cafeteria UZH Botanischer Garten", "Botanischer Garten"],
            "Cafeteria UZH Plattenstrasse": ["Cafeteria UZH Plattenstrasse", "Plattenstrasse", "BWL"]}

        # Log messages to the server to get insights about user activities beside the print statements
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        # Log data to file FoodBot.log
        self.logger = logging.getLogger(__name__)
        fh = logging.FileHandler('CrispyBeefAlert.log')
        fh.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)

    def setConfig(self, configfile: str) -> None:
        # Read my personal bot token out of the token.txt file which is not uploaded to github, and hand it to the updater.
        config = open(configfile, "r")
        for line in config:
            if line.startswith("TOKEN"):
                self.TOKEN = line.split("TOKEN: ")[1].rstrip()
            if line.startswith("JSONPATH:"):
                self.JSONPATH = line.split("JSONPATH: ")[1].rstrip()

    def validateConfig(self) -> bool:
        valid = True
        if self.TOKEN is None:
            print("TOKeN NOT set")
            valid = False
        elif self.JSONPATH is None:
            print("JSONPATH NOT set")
        return valid

    def startBot(self) -> None:
        updater = Updater(self.TOKEN)
        dispatcher = updater.dispatcher

        # Tell dispatcher which functions are to execute according to which user commands
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))
        dispatcher.add_handler(CommandHandler("hilfe", self.help))
        dispatcher.add_handler(CommandHandler("save", self.save))
        dispatcher.add_handler(CommandHandler("delete", self.delete))
        dispatcher.add_handler(MessageHandler(Filters.command, self.unknown))

        # Handler that listens to user messages as text and reacts to it
        dispatcher.add_handler(MessageHandler(Filters.text, self.listen))

        # Error handling that calls the error function to log the error messages
        dispatcher.add_error_handler(self.error)

        # Start bot
        updater.start_polling()

        # Keep the bot alive even though nobody is requesting anything
        print("Bot has booted up")
        updater.idle()

    # function that is executed when the user types /start
    def start(self, bot, update):
        # Sending some welcome messages and instructions about the bot usage
        print(update.message.chat_id)
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Willkommen beim Crispy Beef Alert. \n\n'
                'Speichere deine Lieblingsmenus deiner Stamm-Mensa und bekomme eine Nachricht sobald dein '
                'Wunschgericht wieder auf de Menu-Karte steht. \n\n'
                'Um ein Menu zu speichern \nschreibe /save <Mensa>, <Menu> \n'
                'Beispiel: /save Clausiusbar, Crispy Beef \n\n'
                'Wenn du für ein Gericht keinen Alarm mehr bekommen möchtest \nschreibe /delete <Mensa>, <Menu>\n',
            parse_mode=telegram.ParseMode.MARKDOWN
        )


    # function that is executed when the user types /help
    def help(self, bot, update):
        # send back  help instructions
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Um ein Menu zu speichern \nschreibe /save <Mensa>, <Menu> \n'
                'Beispiel: /save Clausiusbar, Crispy Beef \n\n'
                'Wenn du für ein Gericht keinen Alarm mehr bekommen möchtest, \nschreibe /delete <Mensa>, <Menu> \n'
                'Beispiel: /delete Clausiusbar, Crispy Beef',
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    def delete(self, bot, update):
        """
        Delete entry from subscription JSON
        :param bot: Bot
        :param update: Bot-Update (Message)
        :return: Nothing
        """
        response = update.message.text
        mensa, menu = 0, 0
        # Check if command present
        print("delete request")
        # search for known mensa name
        found = False
        for key, value in self.MENSA_ALIAS.items():
            for alias in value:
                for word in response.split():
                    print(alias)
                    print(word)
                    if fuzz.token_set_ratio(alias, word) > 50:
                        mensa = self.MENSA[key]
                        found = True

                        # search for menu name which should listed after a ","
                        try:
                            menu = response.split(',')[1]
                            # local path concatenate with relative path of json
                            my_path = os.path.abspath(os.path.dirname(__file__))
                            newpath = os.path.join(my_path, self.JSONPATH)
                            # read in json
                            with open(newpath) as f:
                                data = json.load(f)
                            # check json for key of mensa, if not present create empty one
                            if str(mensa) in data:
                                # check json for menu for that mensa
                                if menu in data[str(mensa)]:
                                    # add chat id to that mensa-menu combination
                                    list = data[str(mensa)][menu]
                                    list.remove(update.message.chat_id)
                                    data[str(mensa)][menu] = list
                                # remove key if list is empty
                                if len(data[str(mensa)][menu]) <= 0:
                                    del data[str(mensa)][menu]
                                    msg = "'"+str(menu)+"' gelöscht für '"+str(key)+"'."
                                    sendMessage(msg, update.message.chat_id, self.TOKEN)
                            data["lastUpdate"] = str(datetime.datetime.now())
                            # save updated json
                            with open(self.JSONPATH, 'w') as jsonFile:
                                json.dump(data, jsonFile)
                        except:
                            if response.count(",") < 1:
                                msg = "Bitte stelle sicher das du den Namen der Mensa und das Menu mit einem Komma (',') trennst."
                                sendMessage(msg, update.message.chat_id, self.TOKEN)
                            else:
                                msg = "Leider ist etwas schief gelaufen, bitte überprüfe deine Eingabe. Schreibe /help für " \
                                      "eine Anleitung zur korrekten Eingabe."
                                sendMessage(msg, update.message.chat_id, self.TOKEN)
        if not found:
            msg = "Leider wurde keine passende Mensa in unserer Datenbank gefunden."
            sendMessage(msg, update.message.chat_id, self.TOKEN)


    def save(self, bot, update):
        response = update.message.text
        mensa, menu = 0, 0
        # Check if command present
        print("New save request")
        # search for known mensa name
        found = False
        for key, value in self.MENSA_ALIAS.items():
            for alias in value:
                for word in response.split():
                    print(alias)
                    print(word)
                    if fuzz.token_set_ratio(alias, word) > 50:
                        print("FOUND")
                        found = True
                        mensa = self.MENSA[key]
                        # search for menu name which should be between two "
                        try:
                            menu = response.split(',')[1]
                            # local path concatenate with relative path of json
                            my_path = os.path.abspath(os.path.dirname(__file__))
                            newpath = os.path.join(my_path, self.JSONPATH)
                            # read in json
                            with open(newpath) as f:
                                data = json.load(f)

                            # check json for key of mensa, if not present create empty one
                            if str(mensa) not in data:
                                data[mensa] = {}

                            # check json for menu for that mensa, if not create empty list
                            if menu not in data[str(mensa)]:
                                data[str(mensa)][menu] = []

                            # add chat id to that mensa-menu combination if not present
                            if update.message.chat_id not in data[str(mensa)][menu]:
                                data[str(mensa)][menu].append(update.message.chat_id)
                                msg = "'"+str(menu)+" ' gespeichert für '"+str(key)+"'."
                                sendMessage(msg, update.message.chat_id, self.TOKEN)
                            # update last edited key of json
                            data["lastUpdate"] = str(datetime.datetime.now())
                            # save updated json
                            with open(self.JSONPATH, 'w') as jsonFile:
                                json.dump(data, jsonFile)
                        except:
                            if response.count(",") < 1:
                                msg = "Bitte stelle sicher das du den Namen der Mensa und das Menu mit einem Komme (',') trennst."
                                sendMessage(msg, update.message.chat_id, self.TOKEN)
                            else:
                                msg = "Leider ist etwas schief gelaufen, bitte überprüfe deine Eingabe. Schreibe /help für " \
                                      "eine Anleitung zur korrekten Eingabe."
                                sendMessage(msg, update.message.chat_id, self.TOKEN)
        if not found:
            msg = "Leider wurde keine passende Mensa in unserer Datenbank gefunden."
            sendMessage(msg, update.message.chat_id, self.TOKEN)

    # function reads the users messages
    def listen(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text='I have no news for you. I will message you as soon as I know more',
                         parse_mode=telegram.ParseMode.MARKDOWN)


    # function that is being executed when an error occurs
    def error(self, bot, update, error):
        # Logg all errors as warnings as well as the current update to analyse it later on
        self.logger.warning('Update "%s" caused error "%s"', update, error)

    # Reacting to unknown commands via printing help
    def unknown(self, bot, update):
        self.help(bot, update)


    #def sendMessage(self, msg, chat_id):
        """
        Send a mensage to a telegram user specified on chatId
        chat_id must be a number!
        """
        #bot = telegram.Bot(token=self.TOKEN)
        #bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

def sendMessage(msg, chat_id, token):
    """
    Send a mensage to a telegram user specified on chatId
    chat_id must be a number!
    """
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

"""

"""





if __name__ == '__main__':
    AlertBot = MenuAlertBot()
    AlertBot.setConfig("config.txt")
    if AlertBot.validateConfig():
        AlertBot.startBot()
        print("Bot has booted up")
    else:
        print("ERROR: invalid Config")
