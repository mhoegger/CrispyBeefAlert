import sqlite3
import json
import os
from DataBaseHandler import DataBaseHandler


class Setup:
    def __init__(self, configfile: str, list_of_mensa_json: str):
        with open(configfile) as f:
            self.config_json = json.load(f)

        # Create DataBase
        db_file = self.config_json["db_path"]
        self.db = DataBaseHandler(db_file)
        try:
            self.conn = sqlite3.connect(db_file)
        except RuntimeError as e:
            print(e)

        c = self.conn.cursor()

        # Create DataBase
        self.db.createDataBase()


        for path in list_of_mensa_json:
            uni = os.path.splitext(os.path.basename(path))[0]  # get the filename as the university name
            with open(path) as f:
                mensa_dict = json.load(f)
            for mensa_key in mensa_dict:
                print(mensa_key, mensa_dict[mensa_key]["id"], uni)
                try:
                    c.execute("""INSERT INTO available_mensa (mensa, online, university) VALUES (?, ?, ?);""",
                              (mensa_key, mensa_dict[mensa_key]["id"], uni))
                except:
                    print("already saved")
                for mensa_alias in mensa_dict[mensa_key]["alias"]:
                    try:
                        c.execute("""INSERT INTO mensa_alias (mensa, alias) VALUES (?, ?);""", (mensa_key, mensa_alias))
                    except:
                        print("already saved")
        self.conn.commit()

        # load previous data
        try:
            with open(self.config_json["json_path"]) as f:
                self.json_db = json.load(f)
            key_list = [*self.json_db]
            print("key_list",key_list)
            key_list.remove("lastUpdate")
            for mensa_dict_key in key_list:
                value_dict = self.json_db[mensa_dict_key]
                menus = [*value_dict]
                mensa_name = self.db.get_mensa_by_online_id(mensa_dict_key)
                for menu in menus:
                    for user_id in value_dict[menu]:
                        self.db.write_alert(user_id, mensa_name, menu)
        except e:
            print(e)
            print("no previous data loaded.")


if __name__ == "__main__":
    setup = Setup("./config.json", ["./ETH_Mensa.json", "./UZH_Mensa.json"])

