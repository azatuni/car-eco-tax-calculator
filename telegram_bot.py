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
    start_keyboard = [["/start"]]
    horse_powers_keyboard = [["156"], ["234"]]
    prod_year_keyboard = [[str(datetime.datetime.today().year - year)]
                          for year in range(8)]
    prod_year_keyboard.append([f"մինչև {prod_year_keyboard[-1][0]}"])
    # Regex pattern for horse powers and production year
    regex_pattern = re.compile(r"(մինչև\s)?([0-9]{2,4})")
    offset = 0
    updates = []
    chat_ids = []
    chat_history = {}
    url, payload, keyboard, reply_text = None, None, None, None

    def __init__(self, token):
        api_url = f"https://api.telegram.org/bot{token}/"
        self.api_send_message_url = f"{api_url}sendMessage"
        self.api_get_updates_url = f"{api_url}getUpdates"

    def __request(self) -> dict:
        """Make a http call and return result object if it was successful"""
        headers = {
            "accept": "application/json",
            "User-Agent": "AutoEcoTaxBot",
            "content-type": "application/json"
        }

        response = requests.post(self.url,
                                 json=self.payload,
                                 headers=headers).json()
        logging.debug(f"Payload: {self.payload}")
        logging.debug(f"Response: {response}")
        if not response["ok"]:
            raise TelegramBotApiError(f"Telegram API response "
                                      f"not ok: {response}")
        return response["result"]

    def get_updates(self) -> None:
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
            logging.error(f"Failed sent message {self.reply_text} to "
                          f"{self.chat_id} chat id, error{api_error}")
            return False

    def add_updates_to_queue(self) -> None:
        """Add updates to chat_ids and chat_history"""
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

    def cleanup_old_chats(self):
        cleanup_indexes = []
        for chat_id_index, chat_id in enumerate(self.chat_ids):
            prod_year = self.chat_history[chat_id]["prod_year"]
            horse_power = self.chat_history[chat_id]["horse_powers"]
            replied = self.chat_history[chat_id]["processed"]
            if prod_year is not None and horse_power is not None and replied:
                del self.chat_history[chat_id]
                logging.info(f"removed {chat_id} processed chat from queue")
                cleanup_indexes.append(chat_id_index)
        if cleanup_indexes:
            for index in cleanup_indexes:
                del self.chat_ids[index]

    def extract_from_message(self, field) -> bool:
        """Try to extract from message horse_powers of prod_year"""
        if self.regex_pattern.findall(self.message):
            self.chat_history[self.chat_id][field] = \
                int(self.regex_pattern.findall(self.message)[0][1])
            return True
        return False

    def prod_year_response_helper(self) -> None:
        """Method for set prod year keyboard and reply_text"""
        self.keyboard = self.prod_year_keyboard
        self.reply_text = "մուտքագրեք մեքենայի արտադրման տարեթիվը"

    def horse_powers_response_helper(self) -> None:
        self.keyboard = self.horse_powers_keyboard
        self.reply_text = "մուտքագրեք մեքենայի շարժիչի ձիաուժերի քանակը"

    def process_chat(self):
        """Process chat message"""
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
                self.prod_year_response_helper()
                # Reset counters
                self.chat_history[chat_id]["prod_year"] = None
                self.chat_history[chat_id]["horse_powers"] = None
                if self.send_message():
                    logging.info(f"Replied to message: {self.reply_id}")
                continue
            elif self.prod_year is None and \
                    not self.extract_from_message("prod_year"):
                self.prod_year_response_helper()
                if self.send_message():
                    logging.info(f"Replied to message: {self.reply_id}")
                continue
            elif self.prod_year is None and \
                    self.extract_from_message("prod_year"):
                self.horse_powers_response_helper()
                self.send_message()
                continue
            elif self.horse_powers is None and \
                    not self.extract_from_message("horse_powers"):
                self.horse_powers_response_helper()
                self.send_message()
                continue
            elif self.prod_year and self.horse_powers:
                try:
                    tax = CarEcoTax(self.prod_year,
                                    self.horse_powers).calculate()
                    self.reply_text = f"Վճարման ենթակա բնապահպանության " \
                                      f"հարկը կազմում է` {tax} ֏"
                    self.keyboard = None
                    logging.info(f"Calculate {tax} tax for {self.prod_year} "
                                 f"year and {self.horse_powers} hp")
                except CarEcoTaxProdYearError as year_error:
                    logging.info(f"{year_error}")
                    self.reply_text = f"մուտքագրված արտադրման " \
                                      f"տարեթիվը {self.prod_year} սխալ է"
                    self.chat_history[chat_id]["prod_year"] = None
                except CarEcoTaxHorsePowerError as hp_error:
                    self.reply_text = f"մուտքագրված {hp_error} ձիաուժը սխալ է"
                    self.chat_history[chat_id]["horse_powers"] = None
                self.send_message()
                continue
        self.cleanup_old_chats()

    def run(self) -> None:
        """Primary method for running bot"""
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
        logging.error("TELEGRAM_BOT_TOKEN env var not set. Cannot get token")
        sys.exit(1)
    bot = TelegramBot(token)
    logging.info("Starting Telegram Bot...")
    while True:
        time.sleep(1)
        bot.run()


if __name__ == "__main__":
    main()
