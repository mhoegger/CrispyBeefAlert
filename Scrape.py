import requests
from bs4 import BeautifulSoup
import re
import datetime


class Menu():

    def __init__(self):
        self.MensaDict = None
        self.baseUrl = None

    def scrapeAll(self, date):
        dict = {}
        for name, id in self.MensaDict.items():
            mensaMenu = self.scrape(date, str(id))
            dict[str(id)]=mensaMenu
            #print(dict)
        return dict


    def scrape(self, date, id):
        return None

    def getDayRelation(self, menuWeekDay):
        relations = "notFound"
        todaysWeekday = datetime.datetime.today().weekday()
        if menuWeekDay == todaysWeekday:
            relations = "Today"
        elif menuWeekDay - todaysWeekday > 0 and c - todaysWeekday == 1:
            relations = "Tomorrow"
        elif menuWeekDay - todaysWeekday < 0 and (menuWeekDay+7) - todaysWeekday == 1:
            relations = "Tomorrow"
        elif menuWeekDay - todaysWeekday > 0 and menuWeekDay - todaysWeekday == 2:
            relations = "Day after Tomorrow"
        elif menuWeekDay - todaysWeekday < 0 and (menuWeekDay + 7) - todaysWeekday == 2:
            relations = "Day after Tomorrow"
        else:
            relations = menuWeekDay
        return relations
        #print(todaysWeekday)

class ETHMenu(Menu):


    def __init__(self):
        self.MensaDict = {"Clausiusbar": 4, "Dozentenfoyer": 6, "food&lab": 28, "Foodtrailer": 9, "G-ESSbar": 11,
                    "Polyterrasse": 12, "Polysnack": 13, "Tannenbar": 14}
        self.baseUrl = "https://www.ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerWeek.html"

    def scrape(self, date, id):
        url = self.baseUrl
        payload = {"language": 'de', "date": date, "id": id}
        http = requests.get(
            url, params=payload, headers={'User-Agent': 'Mozilla/5.0'}).text
        menuDiv = BeautifulSoup(http, "html.parser").find("div",{"class":"table-matrix meals"})
        # 0th column is for menu Type, 1st for Monday, 2nd for Tuesday ...
        #print(menuDiv)
        menus = menuDiv.find_all("tr")
        #print(menus)
        del menus[::2]
        #print(menus)
        #print(menus)

        menuNames = []
        for menu in menus:
            days = menu.find_all("td")
            #print(days)
            perDay = []
            for day in days[1:6]:
                #print(day)
                #print(re.search(r'<td>(.*?)<br/>', str(day)).group(1))
                perDay.append((re.search(r'<td>(.*?)</td>', str(day)).group(1)).replace("<br/>", " "))
            menuNames.append(perDay)
        #print(menuNames[0:4])

        return menuNames[0:4]
            #menuDescriptions[n] = re.search(r'<p>\s+(.*?) <br/><br/>', str(menuDescriptions[n])).group(1)


class UZHMenu(Menu):

    def __init__(self):
        #super.__init__(UZHMensa, UZHBaseUrl)
        self.MensaDict = {"Mercato UZH Zentrum": "zentrum-mercato", "Mercato UZH Zentrum Abend": "zentrum-mercato-abend",
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
        self.baseUrl = "https://www.mensa.uzh.ch/de/menueplaene/"

    def scrape(self, date, id):
        allDays={"montag", "dienstag", "mittwoch", "donnerstag", "freitag"}
        url = self.baseUrl+id+"/"
        payload = {}
        for day in allDays:
            url=url+str(day)+".html"
            print(url)
            http = requests.get(
                url, params=payload, headers={'User-Agent': 'Mozilla/5.0'}).text
            print(http)
            menuDiv = BeautifulSoup(http, "html.parser").find("div", {"class": "table-matrix meals"})
            # 0th column is for menu Type, 1st for Monday, 2nd for Tuesday ...
            print(menuDiv)
            menus = menuDiv.find_all("tr")
            # print(menus)
            del menus[::2]
            # print(menus)
            # print(menus)

            menuNames = []
            for menu in menus:
                days = menu.find_all("td")
                # print(days)
                perDay = []
                for day in days[1:6]:
                    # print(day)
                    # print(re.search(r'<td>(.*?)<br/>', str(day)).group(1))
                    perDay.append((re.search(r'<td>(.*?)</td>', str(day)).group(1)).replace("<br/>", " "))
                menuNames.append(perDay)
            # print(menuNames[0:4])

        return menuNames[0:4]
        # menuDescriptions[n] = re.search(r'<p>\s+(.*?) <br/><br/>', str(menuDescriptions[n])).group(1)


if __name__ == "__main__":
    newMenu = UZHMenu()
    newMenu.scrape("2019-04-06","zentrum-mensa")