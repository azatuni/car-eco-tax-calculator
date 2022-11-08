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
    horse_powers_keyboard = [["0 - 50"],
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

    def __init__(self, token):
        api_url = f"https://api.telegram.org/bot{token}/"
        self.api_send_message_url = f"{api_url}sendMessage"
        self.api_get_updates_url = f"{api_url}getUpdates"
        self.offset = 0
        self.updates = []
        self.chat_ids = []
        self.chat_history = {}

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

    def send_message(self, chat_id: int, reply_id: int, message: str, keyboard=None) -> bool:
        """Try to sent message and return True if it successfully sent"""
        self.url = self.api_send_message_url
        self.payload = {
            "chat_id": chat_id,
            "reply_to_message_id": reply_id,
            "text": message
        }
        if keyboard:
            self.payload["parse_mode"] = "Markdown"
            self.payload["reply_markup"] = {"keyboard": keyboard,
                                            "one_time_keyboard": True,
                                            "resize_keyboard": True}
        try:
            sent_response = self.__request()
            logging.info(f"Sent message: {sent_response}")
            self.chat_history[chat_id]["processed"] = True
            return True
        except TelegramBotApiError as api_error:
            logging.error(f"Failed sent message {message} to {chat_id} chat id, "
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

    def extract_prod_year(self, text):
        if self.prod_year_pattern.findall(text):
            return int(self.prod_year_pattern.findall(text)[0][1])
        else:
            return None

    def extract_horse_powers(self, text):
        if self.horse_powers_pattern.findall(text):
            return int(self.horse_powers_pattern.findall(text)[0][0])
        else:
            return None

    def process_chat(self):
        # ToDo: Refactor this class, add queue cleaner
        for chat_id in self.chat_ids:
            message = self.chat_history[chat_id]["last_message"]
            message_id = self.chat_history[chat_id]["last_message_id"]
            replied = self.chat_history[chat_id]["processed"]
            prod_year = self.chat_history[chat_id]["prod_year"]
            horse_powers = self.chat_history[chat_id]["horse_powers"]
            if message == "/start" and not replied:
                reply_text = "մուտքագրեք մեքենայի արտադրման տարեթիվը"
                keyboard = self.prod_year_keyboard
                # Reset counters
                self.chat_history[chat_id]["prod_year"] = None
                self.chat_history[chat_id]["horse_powers"] = None
                if self.send_message(chat_id, message_id, reply_text, keyboard):
                    logging.info(f"Replied to message: {message_id}")
                print(self.chat_history)
                continue
            elif prod_year is None and not replied and self.extract_prod_year(message) is not None:
                self.chat_history[chat_id]["prod_year"] = self.extract_prod_year(message)
                logging.info(f"Updated chat_id prod_year to {self.chat_history[chat_id]['prod_year']}")
                reply_text = "մուտքագրեք մեքենայի շարժիչի ձիաուժերի քանակը"
                keyboard = self.horse_powers_keyboard
                if self.send_message(chat_id, message_id, reply_text, keyboard):
                    logging.info(f"Replied to message: {message_id}")
                print(self.chat_history)
                continue
            elif prod_year is not None and not replied and horse_powers is None and self.extract_horse_powers(message) is None:
                reply_text = "մուտքագրեք մեքենայի շարժիչի ձիաուժերի քանակը"
                keyboard = self.horse_powers_keyboard
                if self.send_message(chat_id, message_id, reply_text, keyboard):
                    logging.info(f"Replied to message: {message_id}")
                print(self.chat_history)
                continue
            elif prod_year is not None and not replied and self.extract_horse_powers(message) is not None:
                self.chat_history[chat_id]["horse_powers"] = self.extract_horse_powers(message)
                horse_powers = self.extract_horse_powers(message)
                logging.info(f"set horse powers to {horse_powers}")
                logging.info(self.chat_history[chat_id])
                try:
                    tax = CarEcoTax(prod_year, horse_powers).calculate()
                    reply_text = f"Վճարման ենթակա բնապահպանության " \
                                 f"հարկը կազմում է` {tax} ֏"
                except CarEcoTaxProdYearError as year_error:
                    logging.info(f"")
                    reply_text = f"մուտքագրված արտադրման տարեթիվը սխալ է"
                    self.chat_history[chat_id]["prod_year"] = None
                except CarEcoTaxHorsePowerError as hp_error:
                    reply_text = f"մուտքագրված ձիաուժը սխալ է"
                    self.chat_history[chat_id]["horse_powers"] = None

                if self.send_message(chat_id, message_id, reply_text):
                    logging.info(f"Replied to message: {message_id}")
                print(self.chat_history)
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
