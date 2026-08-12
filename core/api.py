import requests
import urllib3

from config.settings import BOT_TOKEN


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


class MaxAPI:

    BASE_URL = "https://platform-api2.max.ru"

    def __init__(self):

        self.headers = {
            "Authorization": BOT_TOKEN,
            "Content-Type": "application/json"
        }

    # ==================================================
    # Информация о боте
    # ==================================================

    def get_me(self):

        return requests.get(
            f"{self.BASE_URL}/me",
            headers=self.headers,
            verify=False
        )

    # ==================================================
    # Получение обновлений
    # ==================================================

    def get_updates(
        self,
        marker=None,
        limit=100,
        timeout=30
    ):

        params = {
            "limit": limit,
            "timeout": timeout
        }

        if marker is not None:

            params["marker"] = marker

        response = requests.get(
            f"{self.BASE_URL}/updates",
            headers=self.headers,
            params=params,
            verify=False
        )

        return response

    # ==================================================
    # Отправка сообщения
    # ==================================================

    def send_message(
        self,
        user_id=None,
        chat_id=None,
        text=""
    ):

        params = {}

        if user_id is not None:

            params["user_id"] = user_id

        if chat_id is not None:

            params["chat_id"] = chat_id

        body = {
            "text": text,
            "format": "html"
        }

        return requests.post(
            f"{self.BASE_URL}/messages",
            headers=self.headers,
            params=params,
            json=body,
            verify=False
        )