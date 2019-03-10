import requests
from bs4 import BeautifulSoup
import re
import datetime


class Menu():
    # dictionary of the supportet mensas
    ETHmensa = {"Clausiusbar":4,"Dozentenfoyer":6,"food&lab":28,"Foodtrailer":9,"G-ESSbar":11,
                "Polyterrasse":12,"Polysnack":13,"Tannenbar":14}

    #Base URL
    ETHurl = "https://www.ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerWeek.html"

    def scrape(self, date, id):
        url = self.ETHurl
        payload = {"language": 'de', "date": date, "id": id}
        http = requests.get(
            url, params=payload, headers={'User-Agent': 'Mozilla/5.0'}).text
        menuDiv = BeautifulSoup(http, "html.parser").find("div",{"class":"table-matrix meals"})
        # 0th column is for menu Type, 1st for Monday, 2nd for Tuesday ...
        print(menuDiv)
        menus = menuDiv.find_all("tr")
        print(menus)
        del menus[::2]
        print(menus)
        #print(menus)

        menuNames = []
        for menu in menus:
            days = menu.find_all("td")
            print(days)
            perDay = []
            for day in days[1:6]:
                print(re.search(r'<td>(.*?)<br/>', str(day)).group(1))
                perDay.append(re.search(r'<td>(.*?)<br/>', str(day)).group(1))
            menuNames.append(perDay)
        print(menuNames[0:4])
        return menuNames[0:4]
            #menuDescriptions[n] = re.search(r'<p>\s+(.*?) <br/><br/>', str(menuDescriptions[n])).group(1)


    def getDayRelation(self):
        todaysWeekday = datetime.datetime.today().weekday()
        print(todaysWeekday)


if __name__ == "__main__":
    newMenu = Menu()
    newMenu.scrape("2019-03-04","4")