import os
import requests
import urllib3
from dotenv import load_dotenv

# Отключаем предупреждение (только для проверки!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

url = "https://platform-api2.max.ru/me"

headers = {
    "Authorization": TOKEN
}

response = requests.get(
    url,
    headers=headers,
    verify=False
)

print("Статус:", response.status_code)
print(response.text)