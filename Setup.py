import sqlite3
import json
import os

class Setup:
    def __init__(self, configfile: str, list_of_mensa_json: str):
        with open(configfile) as f:
            config_json = json.load(f)

        # Create DataBase
        db_file = config_json["db_path"]
        try:
            self.conn = sqlite3.connect(db_file)
        except RuntimeError as e:
            print(e)

        c = self.conn.cursor()

        # create table for available Mensi
        c.execute("""CREATE TABLE IF NOT EXISTS available_mensa ( 
                  mensa text PRIMARY KEY NOT NULL, 
                  online text NOT NULL,
                  university text NOT NULL
                  );""")

        c.execute("""CREATE TABLE IF NOT EXISTS available_menus ( 
                  menu text PRIMARY KEY NOT NULL
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

        for path in list_of_mensa_json:
            uni = os.path.splitext(os.path.basename(path))[0]  # get the filename as the university name
            with open(path) as f:
                mensa_dict = json.load(f)
            for mensa_key in mensa_dict:
                c.execute("""INSERT INTO available_mensa (mensa, online, university) VALUES (?, ?, ?);""",
                          (mensa_key, mensa_dict[mensa_key]["id"], uni))
                for mensa_alias in mensa_dict[mensa_key]["alias"]:
                    c.execute("""INSERT INTO mensa_alias (mensa, alias) VALUES (?, ?);""", (mensa_key, mensa_alias))

        self.conn.commit()

