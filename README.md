LifeCheck v0.0.1

✔ Среда разработки настроена
✔ Git
✔ VS Code
✔ Виртуальное окружение
✔ Конфигурация
✔ Загрузка токена
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

APP_NAME = "LifeCheck"
APP_VERSION = "0.0.1"