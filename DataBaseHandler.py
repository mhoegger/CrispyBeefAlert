import sqlite3
import json
import os
from datetime import datetime

class DataBaseHandler:
    def __init__(self, db_file: str):
        try:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
        except RuntimeError as e:
            print(e)
        self.default_language = "EN"

    def writeMenu(self, user_menu: str) -> None:
        """ Saves a menu string into the list of already saved menus.

        :param user_menu: name of the menu
        :type user_menu: String

        :return: Void
        """
        c = self.conn.cursor()
        print(user_menu)
        c.execute("""INSERT INTO available_menus (menu) VALUES (?);""", (user_menu,))
        self.conn.commit()

    def write_alert(self, chat_id: int, found_mensa: str, user_menu: str) -> None:
        """ Save alert with menu, mensa and user id to the database

        :param chat_id: id of the user
        :type chat_id: Integer
        :param found_mensa: Mensa for which user wants to save alert
        :type found_mensa: String
        :param user_menu: Menu that the User wants to save
        :type user_menu: String
        :return:
        """
        c = self.conn.cursor()
        c.execute("""INSERT INTO saved_alerts (user_id, mensa, menu) VALUES (?, ?, ?);""",
                  (chat_id, found_mensa, user_menu))
        self.conn.commit()

    def delete_alert(self, chat_id: int, found_mensa: str, user_menu: str) -> None:
        c = self.conn.cursor()
        c.execute("""DELETE FROM saved_alerts WHERE user_id = ? AND mensa = ? AND menu = ?""",
                  (chat_id, found_mensa, user_menu))
        self.conn.commit()

    def isAlertSaved(self, chat_id: int, user_mensa: str, user_menu: str) -> bool:
        c = self.conn.cursor()
        c.execute('''SELECT id, user_id, mensa, menu FROM saved_alerts 
                    WHERE user_id = ? AND mensa = ? AND menu = ?''', (chat_id, user_mensa, user_menu))
        resp = c.fetchall()
        return len(resp) > 0 and len(resp[0]) > 0

    def selectMensaAlias(self) -> list:
        c = self.conn.cursor()
        c.execute('''SELECT mensa, alias FROM mensa_alias''')
        res = c.fetchall()
        print(res)
        return res

    def countAlerts(self):
        c = self.conn.cursor()
        c.execute('''SELECT mensa, menu, sub_count FROM (
            SELECT mensa, menu, COUNT(DISTINCT user_id) AS sub_count FROM saved_alerts GROUP BY mensa, menu);'''),
        res = c.fetchall()
        print(res)
        return res

    def write_user(self, chat_id):
        c = self.conn.cursor()
        c.execute("""INSERT INTO users (user_id, language) VALUES (?, ?);""",
                  (chat_id, self.default_language))
        self.conn.commit()

    def is_user_saved(self, chat_id):
        c = self.conn.cursor()
        c.execute('''SELECT user_id FROM users 
                    WHERE user_id = ?''', (chat_id,))
        return len(c.fetchall()) > 0

    def get_user_language(self, chat_id):
        c = self.conn.cursor()
        print(chat_id)
        c.execute('''SELECT language FROM users
                    WHERE user_id = (?)''', (chat_id,))
        res = c.fetchall()[0][0]
        return res

    def change_user_language(self, chat_id, language):
        c = self.conn.cursor()
        c.execute('''UPDATE users SET language=? WHERE user_id=?;''', (language, chat_id))
        self.conn.commit()


    def selectMenus(self) -> list:
        c = self.conn.cursor()
        c.execute('''SELECT menu FROM available_menus''')
        res = c.fetchall()
        print(res)
        list = []
        for entry in res:
            list.append(entry[0])
        print(res)
        return list

    def get_universities(self):
        c = self.conn.cursor()
        c.execute('''SELECT DISTINCT university FROM available_mensa ''')
        res = c.fetchall()
        print(res)
        list = []
        for entry in res:
            list.append(entry[0])
        print(res)
        return list


    def get_mensa_by_uni(self, uni) -> list:
        c = self.conn.cursor()
        c.execute('''SELECT mensa FROM available_mensa 
                    WHERE university = (?)''', (uni,))
        res = c.fetchall()
        list = []
        for entry in res:
            list.append(entry[0])
        print(res)
        return list

    def get_mensainfo_by_uni(self, uni) -> list:
        c = self.conn.cursor()
        c.execute('''SELECT mensa, online FROM available_mensa 
                    WHERE university = (?)''', (uni,))
        res = c.fetchall()
        list = []
        for entry in res:
            list.append(entry)
        print(res)
        return list

    def get_useralert_by_mensa_and_menu(self, mensa, menu) -> list:
        c = self.conn.cursor()
        c.execute('''SELECT user_id FROM saved_alerts 
                    WHERE mensa = (?) AND menu = (?)''', (mensa, menu))
        res = c.fetchall()
        list = []
        for entry in res:
            list.append(entry[0])
        print(res)
        return list



    def write_message(self, chat_id: int, message: str):
        """ Save message to the database

        :param chat_id:
        :type chat_id: Integer
        :param message:
        :type message: String

        :return:
        """
        c = self.conn.cursor()
        c.execute("""INSERT INTO messages (user_id, message, timestamp) VALUES (?, ?, ?);""",
                  (chat_id, message, datetime.now()))
        self.conn.commit()

    def createDataBase(self):

        c = self.conn.cursor()

        # create table for available Mensi
        c.execute("""CREATE TABLE IF NOT EXISTS available_mensa ( 
                  id integer PRIMARY KEY AUTOINCREMENT,
                  mensa text NOT NULL, 
                  online text NOT NULL,
                  university text NOT NULL
                  );""")

        c.execute("""CREATE TABLE IF NOT EXISTS available_menus ( 
                  id integer PRIMARY KEY AUTOINCREMENT,
                  menu text NOT NULL
                  );""")

        # create table for alias
        c.execute("""CREATE TABLE IF NOT EXISTS mensa_alias ( 
                  id integer PRIMARY KEY AUTOINCREMENT,
                  mensa text NOT NULL, 
                  alias text NOT NULL,
                  FOREIGN KEY (mensa) REFERENCES available_mensa (mensa)
                  );""")

        # create table for saved alerts
        c.execute("""CREATE TABLE IF NOT EXISTS saved_alerts ( 
                  id integer PRIMARY KEY AUTOINCREMENT,
                  user_id integer NOT NULL, 
                  mensa text NOT NULL,
                  menu text NOT NULL,
                  FOREIGN KEY (mensa) REFERENCES available_mensa (mensa),
                  FOREIGN KEY (menu) REFERENCES available_menus (menu)
                  );""")

        # create table for all messages
        c.execute("""CREATE TABLE IF NOT EXISTS messages ( 
                  id integer PRIMARY KEY AUTOINCREMENT,
                  user_id integer NOT NULL, 
                  message text NOT NULL,
                  timestamp integer NOT NULL
                  );""")

        # create table for user informations
        c.execute("""CREATE TABLE IF NOT EXISTS users ( 
                  id integer PRIMARY KEY AUTOINCREMENT,
                  user_id integer NOT NULL, 
                  language text NOT NULL
                  );""")


        self.conn.commit()

