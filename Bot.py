import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Scrape import Menu
import json
import os
import datetime
from fuzzywuzzy import fuzz
import sqlite3
from CrispyBeefAlert.DataBaseHandler import DataBaseHandler


class MenuAlertBot:
    def __init__(self, configfile: str):

        # Log messages to the server to get insights about user activities beside the print statements
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

        # Log data to file FoodBot.log
        self.logger = logging.getLogger(__name__)
        fh = logging.FileHandler('CrispyBeefAlert.log')
        fh.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)

        # read in json
        with open(configfile) as f:
            self.config_json = json.load(f)

        # Create DataBase
        db_file = self.config_json["db_path"]
        """
        
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
        except RuntimeError as e:
            print(e)
        """
        self.db = DataBaseHandler(db_file)

    def __uniquify_menu(self, user_menu: str) -> str:
        max_score = 0
        found_menu = None
        for db_menu in self.db.selectMensaAlias():
            score = fuzz.token_set_ratio(db_menu, user_menu)
            if score > 50 and score > max_score:
                max_score = score
                found_menu = db_menu
        return found_menu

    def __search_mensa_by_alias(self, user_mensa):
        found_mensi = []
        for db_mensa, db_alias in self.db.selectMensaAlias():
            if fuzz.token_set_ratio(db_alias, user_mensa) > 50 and db_mensa not in found_mensi:
                found_mensi.append(db_mensa)
        return found_mensi

    def save_alert(self, chat_id: int, user_mensa: str, user_menu: str) -> str:
        """saves the requested menu/mensa alert after checking that the alert was not already saved
        and checks for matching menus that are already saved to prevent searching for same menus with slightly different
        names.

        :param chat_id:
        :type chat_id: Integer
        :param user_mensa:
        :type user_mensa: String
        :param user_menu:
        :type user_menu: String

        :return: Success/ Error Message
        :rtype: String
        """
        found_mensi = self.__search_mensa_by_alias(user_mensa)
        if len(found_mensi) > 0:
            found_menu = self.__uniquify_menu(user_menu)
            for found_mensa in found_mensi:
                if not found_menu:
                    # add menu to database
                    print(user_menu)
                    self.db.writeMenu(str(user_menu))
                    self.db.write_alert(chat_id, found_mensa, user_menu)
                else:
                    if self.db.isAlertSaved(chat_id, found_mensa, user_mensa):
                        return "You have already saved an alert for this mensa-menu combination."
                    else:
                        # add menu to database
                        self.db.write_alert(chat_id, found_mensa, found_menu)
        else:
            return "No matching mensa found in our Database. Please type /mensi to see a list of available mensi. " + \
                "If the mensa you meant is in the list please use an appropriate name for it."

    def delete_alert(self, chat_id: int, user_mensa: str, user_menu: str) -> str:
        """delete the requested menu/mensa alert after checking that the alert was already saved.

        :param chat_id:
        :type chat_id: Integer
        :param user_mensa:
        :type user_mensa: String
        :param user_menu:
        :type user_menu: String

        :return: Success/ Error Message
        :rtype: String
        """
        found_mensi = self.__search_mensa_by_alias(user_mensa)
        if len(found_mensi) > 0:
            found_menu = self.__uniquify_menu(user_menu)
            if not found_menu:
                return "Not matching menu found in our database. Are you sure you wrote it correctly?"
            else:
                for found_mensa in found_mensi:
                    if self.db.isAlertSaved(chat_id, found_mensa, found_menu):
                        self.db.delete_alert(chat_id, found_mensa, found_menu)
                    else:
                        return "You have not save this alert therefore it can not be deleted."
        else:
            return "No matching mensa found in our database. Are you sure you wrote it correctly?"

    def get_alert_overview(self, chat_id: int):
        admin_id = self.config_json["admin_chat_id"]
        if (chat_id == admin_id):
            mensa, menu, sub_count = self.db.countAlerts()
            str = ""
            for i, c in sub_count:
                str += "For Menu '{}' at mensa '{}' {} people have a alert\n".format(menu[i], mensa[i], c)
        else:
            return "You are missing the rights for this action."


    def startBot(self) -> None:
        updater = Updater(self.config_json["token"])
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
        self.save_alert(update.message.chat_id, response.split(',')[0], response.split(',')[1])
        """
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
                        msg = "'" + str(menu) + " ' gespeichert für '" + str(key) + "'."
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
        """

    def delete(self, bot, update) -> None:
        """
        Delete entry from subscription JSON
        :param bot: Bot
        :param update: Bot-Update (Message)
        :return: Nothing
        """
        response = update.message.text
        """
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
                            msg = "'" + str(menu) + "' gelöscht für '" + str(key) + "'."
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
        """

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

        # def sendMessage(self, msg, chat_id):
        """
        Send a mensage to a telegram user specified on chatId
        chat_id must be a number!
        """
        # bot = telegram.Bot(token=self.TOKEN)
        # bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


    def sendMessage(self, msg, chat_id, token):
        """
        Send a mensage to a telegram user specified on chatId
        chat_id must be a number!
        """
        bot = telegram.Bot(token=token)
        bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)


    """
    
    """

if __name__ == '__main__':
    AlertBot = MenuAlertBot("./config.json")
    AlertBot.startBot()
    print("Bot has booted up")
