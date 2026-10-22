import requests
import urllib3

from config.settings import BOT_TOKEN


# Отключаем предупреждения о verify=False.
# Настройку TLS пока сохраняем прежней, чтобы это изменение
# не влияло на текущую работу бота.
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


class MaxAPI:

    BASE_URL = "https://platform-api2.max.ru"

    def __init__(self):

        # Создаем отдельную HTTP-сессию.
        self.session = requests.Session()

        # Не использовать системные HTTP_PROXY / HTTPS_PROXY.
        self.session.trust_env = False

        self.headers = {
            "Authorization": BOT_TOKEN,
            "Content-Type": "application/json"
        }

    # ==================================================
    # Информация о боте
    # ==================================================

    def get_me(self):

        return self.session.get(
            f"{self.BASE_URL}/me",
            headers=self.headers,
            verify=False,
            timeout=15
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

        return self.session.get(
            f"{self.BASE_URL}/updates",
            headers=self.headers,
            params=params,
            verify=False,
            timeout=timeout + 10
        )

    # ==================================================
    # Отправка сообщения, при необходимости — с inline-кнопками
    # ==================================================

    def send_message(
        self,
        user_id=None,
        chat_id=None,
        text="",
        buttons=None
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

        # buttons ожидает массив рядов, где каждый ряд — массив кнопок.
        # Каждая кнопка — словарь MAX API, например:
        # {"type": "callback", "text": "Сегодня", "payload": "menu:today"}
        if buttons:
            body["attachments"] = [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": buttons
                    }
                }
            ]

        return self.session.post(
            f"{self.BASE_URL}/messages",
            headers=self.headers,
            params=params,
            json=body,
            verify=False,
            timeout=15
        )

    # ==================================================
    # Подтверждение нажатия inline-кнопки
    # ==================================================

    def answer_callback(self, callback_id):

        if not callback_id:
            return None

        return self.session.post(
            f"{self.BASE_URL}/answers",
            headers=self.headers,
            params={"callback_id": callback_id},
            json={},
            verify=False,
            timeout=15
        )
