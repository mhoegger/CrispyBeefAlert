import requests
from bs4 import BeautifulSoup


class Menu():
    # dictionary of the supportet mensas
    ETHmensa = {"Clausiusbar":4,"Dozentenfoyer":6,"food&lab":28,"Foodtrailer":9,"G-ESSbar":11,
                "Polyterrasse":12,"Polysnack":13,"Tannenbar":14}

    #Base URL
    ETHurl = "https://www.ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerWeek.html"

    def scrape(self, date, id):
        url = self.ETHurl
        print(url)
        payload = {"language": 'de', "date": '2019-03-04', "id": '4'}
        http = requests.get(
            url, params=payload, headers={'User-Agent': 'Mozilla/5.0'}).text
        print(http)
        menuDiv = BeautifulSoup(http, "html.parser").find("div",{"class":"table-matrix meals"})
        # 0th column is for menu Type, 1st for Monday, 2nd for Tuesday ...
        menuNames = menuDiv.find_all("td")[1:5]
        print(menuNames)

if __name__ == "__main__":
    newMenu = Menu()
    newMenu.scrape("2019-03-04","4")