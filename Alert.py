#!/usr/bin/python3


# Script to handle subscribed user and their requested menus
import os
import json
import datetime
from fuzzywuzzy import fuzz
from Scrape import ETHMenu, UZHMenu
import Bot as bot
import datetime
from DataBaseHandler import DataBaseHandler


def main():
    with open('config.json') as f:
        config_json = json.load(f)
    token = config_json["token"]

    db_file = config_json["db_path"]
    db = DataBaseHandler(db_file)

    # scrape menues
    today = datetime.datetime.today().date()
    if today.weekday() == 5: # if saturnday
        today = today + datetime.timedelta(days=2)
    elif today.weekday() == 6: # if saturnday
        today = today + datetime.timedelta(days=1)


    # get all supportet universities
    universities = db.get_universities()

    # scrape instances:
    scrapers = {
        "UZH_Mensa": UZHMenu(),
        "ETH_Mensa": ETHMenu()
    }

    for uni in universities:
        uni_scraper = scrapers[uni]
        mensi = db.get_mensainfo_by_uni(uni)
        for mensa_name,mensa_id in mensi:
            date_to_scrape, days_to_alert = uni_scraper.get_dates_to_scrape()
            #print(mensa_name)
            #print(date_to_scrape.date())
            #print(days_to_alert)
            res = uni_scraper.scrape(date_to_scrape.date(), mensa_id)
            print(res)
            is_weekday = False
            if (len(days_to_alert) == 3):
                # is_weekday
                for day in days_to_alert:
                    day_rel = uni_scraper.getDayRelation(day)
                    menu = res[1][day]
                    print(day_rel)
                    print(menu)


    """
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
    """



if __name__ == '__main__':
    main()