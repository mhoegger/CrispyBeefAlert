#!/usr/bin/python3


# Script to handle subscribed user and their requested menus
import os
import json
import datetime
from fuzzywuzzy import fuzz
from Scrape import ETHMenu, UZHMenu
import Bot as bot
import datetime

ETHmensa = {"Clausiusbar": 4, "Dozentenfoyer": 6, "food&lab": 28, "Foodtrailer": 9, "G-ESSbar": 11,
                    "Polyterrasse": 12, "Polysnack": 13, "Tannenbar": 14}

UZHmensa = {"Mercato UZH Zentrum": "zentrum-mercato", "Mercato UZH Zentrum Abend": "zentrum-mercato-abend",
                         "Mensa UZH Zentrum": "zentrum-mensa", "Mensa UZH Zentrum Lichthof Rondell": "lichthof-rondell",
                         "Mensa UZH Irchel": "mensa-uzh-irchel",
                         "Cafeteria UZH Irchel Atrium": "irchel-cafeteria-atrium",
                         "Cafeteria UZH Irchel Seerose": "irchel-cafeteria-seerose-mittag",
                         "Cafeteria UZH Irchel Seerose": "irchel-cafeteria-seerose-abend",
                         "Mensa UZH Binzmühle": "mensa-uzh-binzmuehle", "Cafeteria UZH Cityport": "mensa-uzh-cityport",
                         "Rämi 59": "raemi59", "Cafeteria Zentrum für Zahnmedizin (ZZM)": "cafeteria-zzm",
                         "Cafeteria UZH Tierspital": "cafeteria-uzh-tierspital",
                         "Cafeteria UZH Botanischer Garten": "cafeteria-uzh-botgarten",
                         "Cafeteria UZH Plattenstrasse": "cafeteria-uzh-plattenstrasse"}
def main():
    print("Currenttime: "+str(datetime.datetime.now()))


    config = open("config.txt", "r")
    for line in config:
        if line.startswith("TOKEN"):
            token = line.split("TOKEN: ")[1].rstrip()
        if line.startswith("JSONPATH:"):
            path = line.split("JSONPATH: ")[1].rstrip()
    tooken = str(token)
    print(tooken)


    # Read path to storage of database JSON (db.json)
    print("Main")
    config = open("config.txt", "r")
    for line in config:
        if line.startswith("JSONPATH:"):
            path = line.split("JSONPATH: ")[1]

    #create Json if not existing yet.
    if not(os.path.exists(path)):
        with open(path, 'w') as jsonFile:
            dict = {}
            dict["lastUpdate"] = str(datetime.datetime.now())
            print(dict)
            json.dump(dict, jsonFile)

    # scrape menues
    today = datetime.datetime.today().date()
    if today.weekday() == 5: # if saturnday
        today = today + datetime.timedelta(days=2)
    elif today.weekday() == 6: # if saturnday
        today = today + datetime.timedelta(days=1)

    InstMenus=[UZHMenu(),ETHMenu()]
    for newMenu in InstMenus:
    #newMenu = ETHMenu()
        allMenus = newMenu.scrapeAll(today)
        print(allMenus)

        with open(path, 'r') as jsonFile:
            subscriptionDict = json.load(jsonFile)
            #print(dict["4"])
            print(newMenu.MensaDict)
            for name, id in newMenu.MensaDict.items():
                if str(id) in subscriptionDict:
                    subscriptionMensaDict = subscriptionDict[str(id)]
                    for wishString, chatId in subscriptionMensaDict.items():
                        for i, days in enumerate(allMenus[str(id)]):
                            #print(days)
                            for menu in days:
                                print(wishString)
                                print(menu)
                                Token_Set_Ratio = fuzz.token_set_ratio(wishString, menu)
                                print(Token_Set_Ratio)
                                #print(wishString+"------------------------------"+menu)
                                #print(Token_Set_Ratio)
                                if Token_Set_Ratio > 95:
                                    print(i)
                                    rel = newMenu.getDayRelation(i)
                                    if rel == "Today":
                                        msg = "Heute gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(tooken)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=tooken)
                                    elif rel == "Tomorrow":
                                        msg = "Morgen gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(tooken)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=tooken)
                                    elif rel == "Day after Tomorrow":
                                        msg = "Übermorgen gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(tooken)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=tooken)
                                    elif today.weekday()==0:
                                        # If Monday tell if in current week menu is available
                                        daystrings = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                                        msg = "Am "+ daystrings[int(rel)] +" gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(tooken)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=tooken)

                        #print(today)
                    #......
            ### for all saved strings
        #Token_Set_Ratio = fuzz.token_set_ratio(Str1,Str2)


if __name__ == '__main__':
    main()