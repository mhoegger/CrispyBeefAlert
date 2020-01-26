#!/usr/bin/python3


# Script to handle subscribed user and their requested menus
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler
import os
import json
import datetime
from fuzzywuzzy import fuzz
from Scrape import ETHMenu, UZHMenu
from DataBaseHandler import DataBaseHandler
from datetime import datetime, timedelta
import re


class MenuAlert:

    def __init__(self):
        with open('config.json') as f:
            self.config_json = json.load(f)
        self.token = self.config_json["token"]

        self.db_file = self.config_json["db_path"]
        self.db = DataBaseHandler(self.db_file)

        # scrape menues
        today = datetime.today().date()
        if today.weekday() == 5:  # if saturnday
            today = today + timedelta(days=2)
        elif today.weekday() == 6:  # if saturnday
            today = today + timedelta(days=1)

        # read in bot message
        with open(self.config_json["message_json"]) as f:
            self.message_json = json.load(f)

        # get all supportet universities
        self.universities = self.db.get_universities()

        # scrape instances:
        self.scrapers = {
            "UZH_Mensa": UZHMenu(),
            "ETH_Mensa": ETHMenu()
        }

        self.non_weekend_menu = ["UZH_Mensa"]

        self.bot = telegram.Bot(token=self.config_json["token"])


    def compare_and_alert(self, alert_menu, menu, mensa_name, day, generic=False):
        menu_normalized = re.sub('\W+', ' ', menu)
        max_token_set_ratio = 0
        for i in range(len(alert_menu)):
            alert_menu_space = alert_menu[:i] + ' ' + alert_menu[i:]
            # compare string of alert-menu and and scraped manu
            token_set_ratio = fuzz.token_set_ratio(menu_normalized, alert_menu_space)
            if token_set_ratio > max_token_set_ratio:
                max_token_set_ratio = token_set_ratio
        print("Compare", alert_menu, menu, max_token_set_ratio)
        # is the correlation is over 96% then raise an alert
        if max_token_set_ratio > 95:
            # get all users which have an alert for this menu.
            alert_user_list = self.db.get_useralert_by_mensa_and_menu(mensa_name, alert_menu)
            for alert_user in alert_user_list:
                if generic:
                    print("Generic", day)
                    self.send_generic_alert_to_user(menu, mensa_name, alert_user, day)
                else:
                    self.send_alert_to_user(menu, mensa_name, alert_user, day)

    def send_alert_to_user(self, menu, mensa_name, alert_user, day):
        day_rel = self.getDayRelation(day)
        lang = self.db.get_user_language(alert_user)
        msg = '\n'.join(self.message_json["alert"][day_rel][lang]) % (menu, mensa_name)
        self.bot.sendMessage(chat_id=alert_user, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

    def send_generic_alert_to_user(self, menu, mensa_name, alert_user, day):
        lang = self.db.get_user_language(alert_user)
        msg = '\n'.join(self.message_json["alert"]["generic_day"][lang]) % (
            self.message_json["days"][str(day)][lang], menu, mensa_name)
        self.bot.sendMessage(chat_id=alert_user, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

    def send_message_to_admin(self, mensa, uni):
        admin_user = self.config_json["admin_chat_id"]
        lang = self.db.get_user_language(admin_user)
        msg = '\n'.join(self.message_json["failed_scrping"][lang]) % (mensa, uni)
        self.bot.sendMessage(chat_id=admin_user, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

    def getDayRelation(self, menu_weekday):
        """ calculate the relation between day of the menu and today, is it today, os ot tomorrow,...?

        :param menu_weekday: datetime representation of the weekday of the manu

        :return: Relation (Today, tomorrow, ....)
        :rtype: String
        """
        today_weekday = datetime.today().weekday()
        if menu_weekday == today_weekday:
            relations = "Today"
        elif menu_weekday - today_weekday > 0 and menu_weekday - today_weekday == 1:
            relations = "Tomorrow"
        elif menu_weekday - today_weekday < 0 and (menu_weekday + 7) - today_weekday == 1:
            relations = "Tomorrow"
        elif menu_weekday - today_weekday > 0 and menu_weekday - today_weekday == 2:
            relations = "Day after Tomorrow"
        elif menu_weekday - today_weekday < 0 and (menu_weekday + 7) - today_weekday == 2:
            relations = "Day after Tomorrow"
        else:
            relations = menu_weekday
        return relations

    def get_menu_for_days(self, days_to_alert, menus_week, mensa_name, generic=False):
        for day in days_to_alert:
            menus = menus_week[day]
            for menu in menus:
                all_alert_menus = self.db.selectMenus()
                for alert_menu in all_alert_menus:
                    self.compare_and_alert(alert_menu, menu, mensa_name, day, generic)

    def get_dates_to_scrape(self):
        """ calculate which days have to be screped today. On weekdays always scrape today and the next two days,
        For weekends scrape the whole upcoming week (Mo-Fr)

        :return: dates for the days to scrape
        """
        today = datetime.today()+timedelta(days=1)
        if today.weekday() == 5:
            # if today is saturday
            return today + timedelta(days=2), [0, 1, 2, 3, 4]
        elif today.weekday() == 6:
            # if today is saturday
            return today + timedelta(days=1), [0, 1, 2, 3, 4]
        else:
            return today, list(range(today.weekday(),today.weekday()+3))

    def main(self):
        # for the set institutes
        for uni in self.universities:
            # get the according scraper
            uni_scraper = self.scrapers[uni]
            # get all the mensi from the Database
            mensi = self.db.get_mensainfo_by_uni(uni)
            # for all mensi get their name and id for, iterate over all the mensi of that institution
            for mensa_name, mensa_id in mensi:
                # get the dates which should be scraped for (dependent on today)
                date_to_scrape, days_to_alert = self.get_dates_to_scrape()
                # scrape the menus for the mensa and the scrape-day (always get the whole week of menus
                status, menus_week = uni_scraper.scrape(date_to_scrape.date(), mensa_id)
                # end loop is scraping was not successful
                if status != "success":
                    self.send_message_to_admin(mensa_name, uni)
                    continue
                if len(days_to_alert) == 3:
                    # is_weekday, so alert with day relation
                    self.get_menu_for_days(days_to_alert, menus_week, mensa_name, generic=False)
                else:
                    # is weekend, so don't scrape for institutes that do not support next weeks menu on weekends
                    if uni in self.non_weekend_menu:
                        continue
                    # on weekend alert with weekday string (not relation)
                    print("days_to_alert", days_to_alert)
                    self.get_menu_for_days(days_to_alert, menus_week, mensa_name, generic=True)


if __name__ == '__main__':
    alert = MenuAlert()
    alert.main()
