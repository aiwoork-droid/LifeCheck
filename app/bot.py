import os
import requests
from dotenv import load_dotenv


class MaxBot:
    def __init__(self):
        load_dotenv()

        self.token = os.getenv("BOT_TOKEN")
        self.base_url = "https://platform-api2.max.ru"

        self.headers = {
            "Authorization": self.token
        }

    def get_me(self):
        response = requests.get(
            f"{self.base_url}/me",
            headers=self.headers,
            verify=False  # Пока только для проверки
        )

        return response