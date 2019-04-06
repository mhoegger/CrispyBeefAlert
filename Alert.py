# Script to handle subscribed user and their requested menus
import os
import json
import datetime
from fuzzywuzzy import fuzz
from Scrape import Menu

ETHmensa = {"Clausiusbar": 4, "Dozentenfoyer": 6, "food&lab": 28, "Foodtrailer": 9, "G-ESSbar": 11,
            "Polyterrasse": 12, "Polysnack": 13, "Tannenbar": 14}

def main():
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
    newMenu = Menu()
    allMenus = newMenu.scrapeAll(today)
    print(allMenus)

    with open(path, 'r') as jsonFile:
        subscriptionDict = json.load(jsonFile)
        #print(dict["4"])
        for name, id in ETHmensa.items():
            if str(id) in subscriptionDict:
                subscriptionMensaDict = subscriptionDict[str(id)]
                for wishString, chatId in subscriptionMensaDict.items():
                    for i, days in enumerate(allMenus[str(id)]):
                        #print(days)
                        for menu in days:
                            Token_Set_Ratio = fuzz.token_set_ratio(wishString, menu)
                            #print(wishString+"------------------------------"+menu)
                            #print(Token_Set_Ratio)
                            if Token_Set_Ratio > 95:
                                print(i)
                                rel = newMenu.getDayRelation(i)
                                if rel == "Today":
                                    print("Heute gibt es folgendes Menu in *"+name+"*: \n"
                                          +menu)
                                elif rel == "Tomorrow":
                                    print("Morgen gibt es folgendes Menu in *"+name+"*: \n"
                                          +menu)
                                elif rel == "Day after Tomorrow":
                                    print("Übermorgen gibt es folgendes Menu in *"+name+"*: \n"
                                          +menu)
                                elif today.weekday()==0:
                                    print("-----------------------")
                                    print(rel)
                                    # If Monday tell if in current week menu is available
                                    daystrings = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
                                    print("Am"+ daystrings[int(rel)] +"gibt es folgendes Menu in *"+name+"*: \n"
                                          +menu)

                    #print(today)
                #......
        ### for all saved strings
    #Token_Set_Ratio = fuzz.token_set_ratio(Str1,Str2)


if __name__ == '__main__':
    main()