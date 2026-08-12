import time

from core.api import MaxAPI
from core.dispatcher import Dispatcher


class LifeCheckBot:

    def __init__(self):
        self.api = MaxAPI()
        self.dispatcher = Dispatcher()
        self.marker = None

    def run(self):

        print("=" * 50)
        print("LifeCheck запущен")
        print("=" * 50)

        while True:

            try:

                response = self.api.get_updates(marker=self.marker)

                if response.status_code != 200:
                    print("Ошибка:", response.status_code)
                    print(response.text)
                    time.sleep(2)
                    continue

                data = response.json()

                self.marker = data.get("marker", self.marker)

                updates = data.get("updates", [])

                for update in updates:
                    self.dispatcher.process(self.api, update)

                time.sleep(1)

            except KeyboardInterrupt:
                print("\nLifeCheck остановлен.")
                break

            except Exception as e:
                print("Ошибка:", e)
                time.sleep(2)