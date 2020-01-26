import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import logging
from Scrape import Menu
import json
import os
import datetime
from fuzzywuzzy import fuzz
import sqlite3
from DataBaseHandler import DataBaseHandler


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

        # read in config json
        with open(configfile) as f:
            self.config_json = json.load(f)

        # read in bot message
        with open(self.config_json["message_json"]) as f:
            self.message_json = json.load(f)
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
        for db_menu in self.db.selectMenus():
            print("db_menu", db_menu)
            score = fuzz.token_set_ratio(db_menu, user_menu)
            print("score", score)
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
        user_language = self.db.get_user_language(chat_id)

        found_mensi = self.__search_mensa_by_alias(user_mensa)
        if len(found_mensi) > 0:
            found_menu = self.__uniquify_menu(user_menu)
            print("founde menu", found_menu)
            for found_mensa in found_mensi:
                if not found_menu:
                    print("add new menu to database")
                    # add new menu to database
                    self.db.writeMenu(str(user_menu))
                    # save alert under user given name
                    self.db.write_alert(chat_id, found_mensa, user_menu)
                    return '\n'.join(self.message_json["save_alert"]["new_menu_saved"][user_language]) % (user_menu, found_mensa)
                else:
                    if self.db.isAlertSaved(chat_id, found_mensa, found_menu):
                        # same menu already saved for this user
                        return '\n'.join(self.message_json["save_alert"]["menu_already_saved"][user_language])
                    else:
                        # save alert under user already know name
                        self.db.write_alert(chat_id, found_mensa, found_menu)
                        return '\n'.join(self.message_json["save_alert"]["similar_Menu"][user_language]) % (found_menu, found_mensa)
        else:
            # no matching mensa found
            return '\n'.join(self.message_json["save_alert"]["no_mensa_found"][user_language])

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
        user_language = self.db.get_user_language(chat_id)


        found_mensi = self.__search_mensa_by_alias(user_mensa)
        if len(found_mensi) > 0:
            found_menu = self.__uniquify_menu(user_menu)
            if not found_menu:
                return '\n'.join(self.message_json["delete_alert"]["no_menu_found"][user_language])
            else:
                for found_mensa in found_mensi:
                    if self.db.isAlertSaved(chat_id, found_mensa, found_menu):
                        # menu alert for user was saved -> delete
                        self.db.delete_alert(chat_id, found_mensa, found_menu)
                        return '\n'.join(self.message_json["delete_alert"]["deleted_alert"][user_language]) % (found_menu, found_mensa)

                    else:
                        return '\n'.join(self.message_json["delete_alert"]["no_saved_alert"][user_language])

        else:
            return '\n'.join(self.message_json["delete_alert"]["no_mensa_found"][user_language])

    def get_mensa(self, chat_id):
        user_language = self.db.get_user_language(chat_id)
        sting_list = self.message_json["mensa_list"][user_language]
        uni_list = self.db.get_universities()
        for uni in uni_list:
            sting_list = sting_list + [uni+"\n"]
            sting_list = sting_list + self.db.get_mensa_by_uni(uni) + ["\n"]
        return '\n'.join(sting_list)


    def get_alert_overview(self, chat_id: int):
        user_language = self.db.get_user_language(chat_id)
        admin_id = self.config_json["admin_chat_id"]
        if (chat_id == admin_id):
            str = ""
            for entry in self.db.countAlerts():
                print(entry)

                mensa, menu, sub_count = entry[0], entry[1], entry[2]
                print(mensa, menu, sub_count)
                str += '\n'.join(self.message_json["overview"][user_language]) % (menu, mensa, sub_count)
            return str
        else:
            return '\n'.join(self.message_json["admin_only"][user_language])


    def save_message(self, chat_id, message):
        self.db.write_message(chat_id, message)
        # forward to admin
        admin_id = self.config_json["admin_chat_id"]
        admin_language = self.db.get_user_language(admin_id)
        self.sendMessage('\n'.join(self.message_json["user_sent_message"][admin_language]) % (chat_id, message), admin_id)

    def change_language(self, chat_id, message):
        user_language = self.db.get_user_language(chat_id)
        if message in self.message_json["available_languages"]:
            if self.db.get_user_language(chat_id) == message:
                return '\n'.join(self.message_json["change_language"]["already_language"][user_language]) % message
            else:
                self.db.change_user_language(chat_id, message)
                user_language = self.db.get_user_language(chat_id)
                return '\n'.join(self.message_json["change_language"]["changed_language"][user_language]) % message
        else:
            return'\n'.join([self.message_json["change_language"]["no_valid_language"][user_language], self.message_json["available_languages"]])

    def start_bot(self) -> None:
        """ Booting up the Bot which listens for user interaction

        :return: None
        """
        updater = Updater(self.config_json["token"])
        dispatcher = updater.dispatcher

        # Tell dispatcher which functions are to execute according to which user commands
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help))
        dispatcher.add_handler(CommandHandler("hilfe", self.help))
        dispatcher.add_handler(CommandHandler("save", self.save))
        dispatcher.add_handler(CommandHandler("delete", self.delete))
        dispatcher.add_handler(CommandHandler("mensa", self.mensa))
        dispatcher.add_handler(CommandHandler("overview", self.overview))
        dispatcher.add_handler(CommandHandler("language", self.language))

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
        """ When user starts interaction with the Bot.
        Welcoming user and tell them how to use the Bot.
        Also save the user to the list of users in the Database
        And save "start" into the list of messages.


        :param bot:
        :param update:
        :return:
        """
        # save user to list of users:
        if not self.db.is_user_saved(int(update.message.chat_id)):
            self.db.write_user(update.message.chat_id)

        # save message, note it as "start"
        self.save_message(update.message.chat_id, "start")

        # Sending some welcome messages and instructions about the bot usage
        msg = self.message_json["welcome"][self.db.get_user_language(update.message.chat_id)]
        bot.send_message(
            chat_id=update.message.chat_id,
            text='\n'.join(msg),
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

        if not self.db.is_user_saved(update.message.chat_id):
            msg = self.message_json["user_not_found"][self.db.get_user_language(update.message.chat_id)]
        else:
            # save message, note it as "start"
            self.save_message(update.message.chat_id, update.message.text)

            response = update.message.text
            msg = self.save_alert(update.message.chat_id, response.split(',')[0], response.split(',')[1])
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )


    def delete(self, bot: telegram.bot.Bot, update: telegram.Update) -> None:
        """
        Delete entry from subscription JSON
        :param bot: Bot
        :param update: Bot-Update (Message)
        :return: Nothing
        """
        # save message, note it as "start"
        self.save_message(update.message.chat_id, update.message.text)

        if not self.db.is_user_saved(update.message.chat_id):
            msg = self.message_json["user_not_found"][self.db.get_user_language(update.message.chat_id)]
        else:
            response = update.message.text
            msg = self.delete_alert(update.message.chat_id, response.split(',')[0], response.split(',')[1])
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    def mensa(self, bot: telegram.bot.Bot, update: telegram.Update) -> None:
        """ Get list of all supported Mensa

        :param bot: Bot
        :param update: Bot-Update (Message)
        :return: Nothing
        """
        # save message
        self.save_message(update.message.chat_id, update.message.text)

        if not self.db.is_user_saved(update.message.chat_id):
            msg = self.message_json["user_not_found"][self.db.get_user_language(update.message.chat_id)]
        else:
            msg = self.get_mensa(update.message.chat_id)
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    def language(self, bot: telegram.bot.Bot, update: telegram.Update) -> None:
        """ Change language

        :param bot: Bot
        :param update: Bot-Update (Message)
        :return: Nothing
        """
        # save message
        self.save_message(update.message.chat_id, update.message.text)

        if not self.db.is_user_saved(update.message.chat_id):
            msg = self.message_json["user_not_found"][self.db.get_user_language(update.message.chat_id)]
        else:
            msg = self.change_language(update.message.chat_id, update.message.text)
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    def overview(self, bot: telegram.bot.Bot, update: telegram.Update) -> None:
        # save message
        self.save_message(update.message.chat_id, update.message.text)

        msg = self.get_alert_overview(update.message.chat_id)
        bot.send_message(
            chat_id=update.message.chat_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

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


    def sendMessage(self, msg, chat_id):
        """
        Send a mensage to a telegram user specified on chatId
        chat_id must be a number!
        """
        bot = telegram.Bot(token=self.config_json["token"])
        bot.sendMessage(chat_id=chat_id, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)



if __name__ == '__main__':
    AlertBot = MenuAlertBot("./config.json")
    AlertBot.start_bot()
    print("Bot has booted up")
