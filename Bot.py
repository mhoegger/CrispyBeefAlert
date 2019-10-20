import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Scrape import Menu
import json
import os
import datetime
from fuzzywuzzy import fuzz
import sqlite3


class MenuAlertBot:
    def __init__(self, list_of_mensa_json: str, configfile: str, db_file: str):
        self.TOKEN = None
        self.JSONPATH = None
        self.MENSA = {}
        for l in list_of_mensa_json:
            self.MENSA = {**self.MENSA, **l}  # combine two dictionaries

        config = open(configfile, "r")
        for line in config:
            if line.startswith("TOKEN"):
                self.TOKEN = line.split("TOKEN: ")[1].rstrip()
            if line.startswith("JSONPATH:"):
                self.JSONPATH = line.split("JSONPATH: ")[1].rstrip()


        # Log messages to the server to get insights about user activities beside the print statements
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        # Log data to file FoodBot.log
        self.logger = logging.getLogger(__name__)
        fh = logging.FileHandler('CrispyBeefAlert.log')
        fh.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)

        # local path concatenate with relative path of json
        my_path = os.path.abspath(os.path.dirname(__file__))
        newpath = os.path.join(my_path, self.JSONPATH)
        # read in json
        with open(configfile) as f:
            config_json = json.load(f)

        # Create DataBase
        db_file = config_json["db_path"]
        try:
            self.conn = sqlite3.connect(db_file)
        except RuntimeError as e:
            print(e)

    def _addMenu(self, user_menu: str) -> str:
        c = self.conn.cursor()
        c.execute('''SELECT (menu) FROM available_menus''')
        max_score = 0
        found_menu = None
        for db_menu in c:
            score = fuzz.token_set_ratio(db_menu, user_menu)
            if score > 50 and score > max_score:
                max_score = score
                found_menu = db_menu
        return found_menu

    def _searchMenuForUser(self, chat_id: int, user_menu: str, user_mensa: str) -> bool:
        c = self.conn.cursor()
        c.execute('''SELECT (id, user_id, mensa, menu) FROM saved_alerts WHERE user_id = ? AND mensa = ? AND menu = ?''', (chat_id, user_mensa, user_menu))
        max_score = 0
        found_menu = None
        for db_menu in c:
            score = fuzz.token_set_ratio(db_menu, user_menu)
            if score > 50 and score > max_score:
                max_score = score
                found_menu = db_menu
        return found_menu

    def _saveAlert(self, chat_id: int, user_mensa: str, user_menu: str) -> str:
        """

        :param chat_id:
        :type chat_id: Integer
        :param user_mensa:
        :type user_mensa: String
        :param user_menu:
        :type user_menu: String

        :return: Success/ Error Message
        :rtype: String
        """
        c = self.conn.cursor()

        c.execute('''SELECT (mensa, alias) FROM mensa_alias''')
        found_mensi = []
        for db_mensa, db_alias in c:
            if fuzz.token_set_ratio(db_alias, user_mensa) > 50 and db_mensa not in found_mensi:
                found_mensi.append(db_mensa)
        if len(found_mensi) <= 0:
            return "No matching mensa found in our Database. Please type /mensi to see a list of available mensi. " + \
                   "If the mensa you meant is in the list please use an appropriate name for it."
        else:
            found_menu = self._addMenu(user_menu)
            if not found_menu:
                for found_mensa in found_mensi:
                    # add menu to database
                    c.execute("""INSERT INTO available_menus (menu) VALUES (?);""", user_menu)
                    c.execute("""INSERT INTO saved_alerts (user_id, mensa, menu) VALUES (?, ?, ?);""",
                              (chat_id, found_mensa, user_menu))
            else:
                for found_mensa in found_mensi:
                    # add menu to database
                    c.execute("""INSERT INTO saved_alerts (user_id, mensa, menu) VALUES (?, ?, ?);""",
                              (chat_id, found_mensa, found_menu))


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
    def start(self, bot: telegram.bot.Bot, update) -> None:
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
    def help(self, bot, update) -> None:
        # send back  help instructions
        bot.send_message(
            chat_id=update.message.chat_id,
            text='Um ein Menu zu speichern \nschreibe /save <Mensa>, <Menu> \n'
                'Beispiel: /save Clausiusbar, Crispy Beef \n\n'
                'Wenn du für ein Gericht keinen Alarm mehr bekommen möchtest, \nschreibe /delete <Mensa>, <Menu> \n'
                'Beispiel: /delete Clausiusbar, Crispy Beef',
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    def save(self, bot: telegram.bot.Bot, update: telegram.Update) -> None:
        """Save a menu-mensa pair for which the communicating user wants to be notified.

        :param bot:
        :type bot: telegram.bot.Bot
        :param update:
        :type update: telegram.Update
        :return: None
        """
        response = update.message.text
        mensa, menu = None, None
        # Check if command present
        print("New save request")
        # search for known mensa name
        found_any = False
        requested_mensa = []
        for key in self.MENSA:
            found = False
            for alias in self.MENSA[key]["alias"]:
                for word in response.split():
                    if fuzz.token_set_ratio(alias, word) > 50:
                        requested_mensa.append(key)
                        found = True
        if len(requested_mensa) > 0:
            # search for menu name which should be after ","
            try:
                menu = response.split(',')[1]
                for mensa in requested_mensa:
                    # check json for key of mensa, if not present create empty one
                    if str(mensa) not in self.json_data:
                        self.json_data[mensa] = {}

                    # check json for menu for that mensa, if not create empty list
                    if menu not in self.json_data[str(mensa)]:
                        self.json_data[str(mensa)][menu] = []

                    # add chat id to that mensa-menu combination if not present
                    if update.message.chat_id not in self.json_data[str(mensa)][menu]:
                        self.json_data[str(mensa)][menu].append(update.message.chat_id)
                        msg = "'"+str(menu)+" ' gespeichert für '"+str(key)+"'."
                        sendMessage(msg, update.message.chat_id, self.TOKEN)
                    # update last edited key of json
                        self.json_data["lastUpdate"] = str(datetime.datetime.now())
                    # save updated json
                    with open(self.JSONPATH, 'w') as jsonFile:
                        json.dump(self.json_data, jsonFile)
            except:
                if response.count(",") < 1:
                    msg = "Bitte stelle sicher das du den Namen der Mensa und das Menu mit einem Komme (',') trennst."
                    sendMessage(msg, update.message.chat_id, self.TOKEN)
                else:
                    msg = "Leider ist etwas schief gelaufen, bitte überprüfe deine Eingabe. Schreibe /help für " \
                          "eine Anleitung zur korrekten Eingabe."
                    sendMessage(msg, update.message.chat_id, self.TOKEN)
        if not found_any:
            msg = "Leider wurde keine passende Mensa in unserer Datenbank gefunden."
            sendMessage(msg, update.message.chat_id, self.TOKEN)

    def delete(self, bot, update) -> None:
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
        found_any = False
        for key in self.MENSA:
            found = False
            for alias in self.MENSA[key]["alias"]:
                for word in response.split():
                    if fuzz.token_set_ratio(alias, word) > 50:
                        mensa = key
                        found = True
            if found:
                found_any = True
                # search for menu name which should listed after a ","
                try:
                    menu = response.split(',')[1]
                    # check json for key of mensa, if not present create empty one
                    if str(mensa) in self.json_data:
                        # check json for menu for that mensa
                        if menu in self.json_data[str(mensa)]:
                            # add chat id to that mensa-menu combination
                            list = self.json_data[str(mensa)][menu]
                            list.remove(update.message.chat_id)
                            self.json_data[str(mensa)][menu] = list
                        # remove key if list is empty
                        if len(self.json_data[str(mensa)][menu]) <= 0:
                            del self.json_data[str(mensa)][menu]
                            msg = "'"+str(menu)+"' gelöscht für '"+str(key)+"'."
                            sendMessage(msg, update.message.chat_id, self.TOKEN)
                    self.json_data["lastUpdate"] = str(datetime.datetime.now())
                    # save updated json
                    with open(self.JSONPATH, 'w') as jsonFile:
                        json.dump(self.json_data, jsonFile)
                except:
                    if response.count(",") < 1:
                        msg = "Bitte stelle sicher das du den Namen der Mensa und das Menu mit einem Komma (',') trennst."
                        sendMessage(msg, update.message.chat_id, self.TOKEN)
                    else:
                        msg = "Leider ist etwas schief gelaufen, bitte überprüfe deine Eingabe. Schreibe /help für " \
                                          "eine Anleitung zur korrekten Eingabe."
                        sendMessage(msg, update.message.chat_id, self.TOKEN)
            if not found_any:
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
