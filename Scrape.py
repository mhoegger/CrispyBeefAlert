import requests
from bs4 import BeautifulSoup
import re
import datetime
import json

class Menu:
    """Class to define the overall structure of a Menu that should be scraped

    """
    def __init__(self):
        self.MensaDict = {}
        self.baseUrl = {}

    def scrapeAll(self, date):
        dict_over_mensi = {}
        for key in self.MensaDict:
            dict_over_mensi[str(self.MensaDict[key]["id"])] = self.scrape(date, str(self.MensaDict[key]["id"]))
        return dict_over_mensi


    def scrape(self, date, id):
        return None

    def getDayRelation(self, menuWeekDay):
        relations = "notFound"
        todaysWeekday = datetime.datetime.today().weekday()
        if menuWeekDay == todaysWeekday:
            relations = "Today"
        elif menuWeekDay - todaysWeekday > 0 and menuWeekDay - todaysWeekday == 1:
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
        #print(todaysWeekday)ddd

class ETHMenu(Menu):
    """ Class to handle the ETH menu plans

    :param path_to_json: path to the JSON file where the different mensi are described with id (which is used in the
    url) and some alias names which might be used by the users.
    :type path_to_json: Path or String
    """

    def __init__(self, path_to_json):
        """constructor method

        set the base url from where the menus should be scraped from
        """
        super().__init__()
        with open(path_to_json) as f:
            ETH_json = json.load(f)
        self.MensaDict = ETH_json
        self.baseUrl = "https://www.ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerWeek.html"

    def scrape(self, date, id):
        """Scrapes the website of the ETH to get the menus for each day and for each mensa.

        :param date: date of the date where the menu should be fetched for
        :type date: Date: YYYY-MM-DD
        :param id: ID of the mensa for with the menu should be fetched
        :type id: Integer

        :return: Status, Menus
        :rtype: String, List of Strings
        """
        url = self.baseUrl
        payload = {"language": 'de', "date": date, "id": id}
        http = requests.get(
            url, params=payload, headers={'User-Agent': 'Mozilla/5.0'}).text
        menu_div = BeautifulSoup(http, "html.parser").find("div",{"class":"table-matrix meals"})
        number_of_days = 5

        try:
            menus = menu_div.find_all("tr")
            del menus[::2]  # The menus are only in every second "tr", so delete the others
            menu_names = [[] for _ in range(number_of_days)]
            for day_menu in menus[:-1]:  # iterate over the different weekdays
                menues = day_menu.find_all("td")
                for k, men in enumerate(menues[1:6]):  # skip first one because it tells the weekday
                    menu_names[k].append((re.search(r'<td>(.*?)</td>', str(men).replace("<h3>", "**").
                                           replace("</h3>", "** ")).group(1)).replace("<br/>", " "))
            return "success", menu_names[0:5]

        except RuntimeError as e:
            print("Error: "+str(e))
            return str(e), [["-"], ["-"], ["-"], ["-"], ["-"]]


class UZHMenu(Menu):
    """ Class to handle the UZH menu plans

    :param path_to_json: path to the JSON file where the different mensi are described with id (which is used in the
    url) and some alias names which might be used by the users.
    :type path_to_json: Path or String
    """

    def __init__(self, path_to_json):
        """constructor method

        set the base url from where the menus should be scraped from
        """
        super().__init__()
        with open(path_to_json) as f:
            UZH_json = json.load(f)
        self.MensaDict = UZH_json
        self.baseUrl = "https://www.mensa.uzh.ch/de/menueplaene/"

    def scrape(self, date, id):
        """Scrapes the website of the UZH to get the menus for each day and for each mensa.

        :param date: date of the date where the menu should be fetched for
        :type date: Date: YYYY-MM-DD
        :param id: ID of the mensa for with the menu should be fetched
        :type id: Integer

        :return: Status, Menus
        :rtype: String, List of Strings
        """
        day_strings = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag"]
        base_url = self.baseUrl+id+"/"
        payload = {}
        all_days_menus = []
        errors = ""
        for day in day_strings:
            url = base_url+str(day)+".html"
            http = requests.get(
                url, params=payload, headers={'User-Agent': 'Mozilla/5.0'}).text
            menu_div = BeautifulSoup(http, "html.parser").find("div", {"class": "newslist-description"})
            try:
                menu_names = menu_div.find_all("h3")
                menus_description = menu_div.find_all("p")[0::2]
                menu_string = []
                if len(menu_names) == len(menus_description):
                    for i in range(len(menu_names)):
                        menu_string.append(str(menu_names[i]).replace("<h3>", "").
                                           replace("</h3>", "").replace("<span>", "").replace("</span>", "") +
                                           "\n"+str(menus_description[i]).replace("<p>", "").replace("</p>", "").
                                           replace("<br/>", ""))
                all_days_menus.append(menu_string)
            except RuntimeError as e:
                errors += str(e) + ", "
                all_days_menus.append(" - ")

        if errors == "":
            return "success", all_days_menus
        else:
            return errors, all_days_menus


if __name__ == "__main__":
    newMenu = ETHMenu('ETH_Mensa.json')
    print(newMenu.scrape("2019-10-19",4))