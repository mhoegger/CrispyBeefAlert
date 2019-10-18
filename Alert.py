#!/usr/bin/python3


# Script to handle subscribed user and their requested menus
import os
import json
import datetime
from fuzzywuzzy import fuzz
from Scrape import ETHMenu, UZHMenu
import Bot as bot
import datetime


def main():
    with open('config.json') as f:
        config_json = json.load(f)




    print("Currenttime: "+str(datetime.datetime.now()))
    config = open("config.txt", "r")
    for line in config:
        if line.startswith("TOKEN"):
            token = str(line.split("TOKEN: ")[1].rstrip())
        if line.startswith("JSONPATH:"):
            path = line.split("JSONPATH: ")[1].rstrip()
        if line.startswith("ADMIN_CHAT:"):
            admin_chat = line.split("ADMIN_CHAT: ")[1].rstrip()

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
                                        print(token)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=token)
                                    elif rel == "Tomorrow":
                                        msg = "Morgen gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(token)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=token)
                                    elif rel == "Day after Tomorrow":
                                        msg = "Übermorgen gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(token)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=token)
                                    elif today.weekday()==0:
                                        # If Monday tell if in current week menu is available
                                        daystrings = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                                        msg = "Am "+ daystrings[int(rel)] +" gibt es folgendes Menu in *"+name+"*: \n"+menu
                                        print(msg)
                                        print(token)
                                        for singleID in chatId:
                                            bot.sendMessage(msg,singleID,token=token)




if __name__ == '__main__':
    main()