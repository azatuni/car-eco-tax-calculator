import sys
import requests
import logging
import time
import datetime
import re
import os
from taxcalc import CarEcoTax
from taxcalc import CarEcoTaxProdYearError
from taxcalc import CarEcoTaxHorsePowerError


class TelegramBotApiError(Exception):
    """Exception class for not OK response in json"""
    pass


class TelegramBot:
    """Telegram Bot main class"""
    horse_powers_keyboard = [["1 - 50"],
                             ["51 - 80"],
                             ["81 - 100"],
                             ["101 - 150"],
                             ["151 - 200"],
                             ["201 - 250"],
                             ["251 - 300"],
                             ["301 ավել"]]
    prod_year_keyboard = [[str(datetime.datetime.today().year - year)]
                          for year in range(8)]
    prod_year_keyboard.append([f"մինչև {prod_year_keyboard[-1][0]}"])
    prod_year_pattern = re.compile(r"(մինչև\s)?([0-9]{2,4})")
    horse_powers_pattern = re.compile(r"([0-9]*)(\s\-\s|\s)?([0-9]{1,3}|ավել)?")
    offset = 0
    updates = []
    chat_ids = []
    chat_history = {}

    def __init__(self, token):
        api_url = f"https://api.telegram.org/bot{token}/"
        self.api_send_message_url = f"{api_url}sendMessage"
        self.api_get_updates_url = f"{api_url}getUpdates"

    def __request(self):
        """Make a http call and return result object if it was successful"""
        headers = {
            "accept": "application/json",
            "User-Agent": "AutoEcoTaxBot",
            "content-type": "application/json"
        }

        response = requests.post(self.url, json=self.payload, headers=headers).json()
        logging.debug(f"Payload: {self.payload}")
        logging.debug(f"Response: {response}")
        if not response["ok"]:
            raise TelegramBotApiError(f"Telegram API response not ok: {response}")
        return response["result"]

    def get_updates(self):
        """Get Updates from telegram"""
        self.url = self.api_get_updates_url
        logging.debug(f"url: {self.url}")
        logging.debug(f"offset: {self.offset}")
        self.payload = {
            "offset": self.offset,
            "timeout": None
        }
        self.updates = self.__request()
        logging.debug(f"All updates from telegram API: {self.updates}")
        # If updates exists add them to queue
        if self.updates:
            self.offset = self.updates[-1]["update_id"] + 1
            logging.info(f"Offset updated to {self.offset}")

    def send_message(self) -> bool:
        """Try to sent message and return True if it successfully sent"""
        self.url = self.api_send_message_url
        self.payload = {
            "chat_id": self.chat_id,
            "reply_to_message_id": self.reply_id,
            "text": self.reply_text
        }
        if self.keyboard:
            self.payload["parse_mode"] = "Markdown"
            self.payload["reply_markup"] = {"keyboard": self.keyboard,
                                            "one_time_keyboard": True,
                                            "resize_keyboard": True}
        try:
            sent_response = self.__request()
            logging.info(f"Sent message: {sent_response}")
            self.chat_history[self.chat_id]["processed"] = True
            return True
        except TelegramBotApiError as api_error:
            logging.error(f"Failed sent message {self.reply_text} to {self.chat_id} chat id, "
                          f"error{api_error}")
            return False

    def add_updates_to_queue(self):
        for update in self.updates:
            chat_id = update["message"]["chat"]["id"]
            message_id = update["message"]["message_id"]
            message_text = update["message"]["text"]
            if chat_id not in self.chat_ids:
                self.chat_ids.append(chat_id)
                self.chat_history[chat_id] = {"last_message": message_text,
                                              "last_message_id": message_id,
                                              "horse_powers": None,
                                              "prod_year": None,
                                              "processed": False}
            else:
                self.chat_history[chat_id]["last_message"] = message_text
                self.chat_history[chat_id]["last_message_id"] = message_id
                self.chat_history[chat_id]["processed"] = False
        # Clean up self.updates
        logging.info(f"chat ids are: {self.chat_ids}")
        logging.info(f"chat_history: {self.chat_history}")
        self.updates = []

    def extract_prod_year(self) -> bool:
        """Try to get prod year from message and set it as self.prod_year"""
        if self.prod_year_pattern.findall(self.message):
            self.chat_history[self.chat_id]["prod_year"] = \
                int(self.prod_year_pattern.findall(self.message)[0][1])

            #self.prod_year = int(self.prod_year_pattern.findall(self.message)[0][1])
            return True
            # return int(self.prod_year_pattern.findall(self.message)[0][1])
        else:
            return False
            # return None

    def extract_horse_powers(self) -> bool:
        if self.horse_powers_pattern.findall(self.message):
            self.chat_history[self.chat_id]["horse_powers"] = \
                int(self.horse_powers_pattern.findall(self.message)[0][0])
            #print(self.horse_powers_pattern.findall(self.message)[0][0])
            # self.horse_powers = int(self.horse_powers_pattern.findall(self.message)[0][0])
            # return int(self.horse_powers_pattern.findall(self.message)[0][0])
            return True
        else:
            return False
            # return None

    def prod_year_response_helper(self):
        self.keyboard = self.prod_year_keyboard
        self.reply_text = "մուտքագրեք մեքենայի արտադրման տարեթիվը"

    def hourse_powers_response_helper(self):
        self.keyboard = self.horse_powers_keyboard
        self.reply_text = "մուտքագրեք մեքենայի շարժիչի ձիաուժերի քանակը"

    def process_chat(self):
        # ToDo: Refactor this class, add queue cleaner
        for chat_id in self.chat_ids:
            self.chat_id = chat_id
            self.message = self.chat_history[chat_id]["last_message"]
            self.reply_id = self.chat_history[chat_id]["last_message_id"]
            self.replied = self.chat_history[chat_id]["processed"]
            self.prod_year = self.chat_history[chat_id]["prod_year"]
            self.horse_powers = self.chat_history[chat_id]["horse_powers"]
            # Don't response to already replied messages
            if self.replied:
                continue
            if self.message == "/start":
                # reply_text = "մուտքագրեք մեքենայի արտադրման տարեթիվը"
                # self.keyboard = self.prod_year_keyboard
                self.prod_year_response_helper()
                # Reset counters
                self.chat_history[chat_id]["prod_year"] = None
                self.chat_history[chat_id]["horse_powers"] = None
                if self.send_message():
                    logging.info(f"Replied to message: {self.reply_id}")
                print(self.chat_history)
                continue
            elif self.prod_year is None and not self.extract_prod_year():
                self.prod_year_response_helper()
                if self.send_message():
                    logging.info(f"Replied to message: {self.reply_id}")
                print(self.chat_history)
                continue
            elif self.prod_year is None and self.extract_prod_year():
                #self.chat_history[chat_id]["prod_year"] = self.prod_year
                self.hourse_powers_response_helper()
                #self.set_get_year_response()
                #self.keyboard = self.prod_year_keyboard
                self.send_message()
                print(self.chat_history)
                continue
            elif self.horse_powers is None and not self.extract_horse_powers():
                self.hourse_powers_response_helper()
                self.send_message()
                print(self.chat_history)
                continue
            elif self.prod_year is not None and self.horse_powers is not None:
                try:
                    tax = CarEcoTax(self.prod_year, self.horse_powers).calculate()
                    self.reply_text = f"Վճարման ենթակա բնապահպանության "\
                                      f"հարկը կազմում է` {tax} ֏"
                    self.keyboard = None
                    logging.info(f"Calculate {tax} tax for {self.prod_year} year and {self.horse_powers} hp")
                except CarEcoTaxProdYearError as year_error:
                    logging.info(f"")
                    self.reply_text = f"մուտքագրված արտադրման տարեթիվը սխալ է"
                    self.chat_history[chat_id]["prod_year"] = None
                except CarEcoTaxHorsePowerError as hp_error:
                    self.reply_text = f"մուտքագրված ձիաուժը սխալ է"
                    self.chat_history[chat_id]["horse_powers"] = None
                self.send_message()
                continue


    def run(self):
        try:
            self.get_updates()
        except TelegramBotApiError as bot_api_error:
            logging.error(bot_api_error)
            self.updates = []
        except requests.exceptions.ConnectionError as con_error:
            logging.error(con_error)
            self.updates = []
        # If updates exists add them to queue
        if self.updates:
            self.add_updates_to_queue()
        else:
            logging.debug(f"No new updates exists: {self.updates}")

        if self.chat_ids:
            self.process_chat()


def main():
    debug = False
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S')
    try:
        token = os.environ['TELEGRAM_BOT_TOKEN']
    except KeyError:
        logging.error(f"TELEGRAM_BOT_TOKEN env var not set cannot get token")
        sys.exit(1)
    bot = TelegramBot(token)
    while True:
        time.sleep(1)
        bot.run()


if __name__ == "__main__":
    main()
