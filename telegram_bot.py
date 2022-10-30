import requests
import logging


class TelegramBotApiError(Exception):
    """Exception class for not OK response in json"""
    pass


class TelegramBot:
    """Telegram Bot main class"""
    def __init__(self, token, debug=False):
        self.api_url = f"https://api.telegram.org/bot{token}/"
        self.offset = 0
        self.message_queue = {}
        self.updates = []
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def __request(self):
        """Make a http call and return result object if it was successful"""
        headers = {
            "accept": "application/json",
            "User-Agent": "AutoEcoTaxBot",
            "content-type": "application/json"
        }

        response = requests.post(self.url, json=self.payload, headers=headers).json()
        logging.debug(f"Payload: {self.payload}")
        logging.debug(response)
        if not response["ok"]:
            raise TelegramBotApiError(f"Telegram API response not ok")
        return response["result"]

    def get_updates(self):
        """
                https: // api.telegram.org / bot5491988468: AAHguJVZg6i6IVW6cugPE7 - 4
                y1Co4LzXDUA / sendMessage?chat_id = 346978321 & text = hello
        """
        self.url = f"{self.api_url}getUpdates"
        logging.debug(f"url: {self.url}")
        logging.debug(f"offset: {self.offset}")
        self.payload = {
            "offset": self.offset,
       #     "limit": None,
            "timeout": None
        }
        self.updates = self.__request()
        logging.debug(self.updates)
        """
        try:
            self.update = self.__request()
        except TelegramBotError as bot_error:
            logging.error(bot_error)
            self.update = []
        except requests.exceptions.ConnectionError as con_error:
            logging.error(con_error)
            self.update = []
        """

        def sendMessage(self, chat_id, text):
            print(1)

    def add_updates_to_queue(self):
        for update in self.updates:
            update_id = update["update_id"]
            message = update["message"]
            if not self.message_queue.get(update_id):
                self.message_queue[update_id] = message
                logging.info(f"{update_id} update id added to queue")
            else:
                logging.info(f"{update_id} update id already exists in queue")
            #self.message_queue[update["update_id"]] = update["message"]
            # Increase offset by one
            # self.offset = update["update_id"] + 1
            logging.info(self.message_queue)

    def send_message(self, chat_id, reply_id, message):
        self.url = f"{self.api_url}sendMessage"
        self.payload = {
            "chat_id": chat_id,
            "reply_to_message_id": reply_id,
            "text": message
        }
        print(message)
        self.updates = self.__request()

    def is_bot_command(self, message):
        try:
            if message["entities"][0]["type"] == "bot_command":
                return True
        except KeyError:
            pass
        return False

    def process_queue(self):
        for msg_id, msg in self.message_queue.items():
            if self.is_bot_command(msg):
                print(f"Bot: {msg}")
            else:
                text = "Please enter bot command"
                print(msg_id, msg)
                self.send_message(msg["chat"]["id"], msg["message_id"], text)
            #self.is_year(msg)

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
            logging.info(f"No new updates exists")

        # If messages exists in queue process them
        if self.message_queue:
            self.process_queue()
        return True



bot = TelegramBot(telegram_bot_token, debug=True)
for i in range(2):
    bot.run()

#print(update)