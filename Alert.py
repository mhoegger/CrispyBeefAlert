# Script to handle subscribed user and their requested menus
import os
import json
import datetime



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


if __name__ == '__main__':
    main()