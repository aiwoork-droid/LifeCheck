import time

from core.api import MaxAPI
from core.dispatcher import Dispatcher


class LifeCheckBot:

    def __init__(self):
        self.api = MaxAPI()
        self.dispatcher = Dispatcher()
        self.marker = None
        self.processed_ids = set()

    def _make_update_id(self, update):
        """Стабильный ID обновления, чтобы не обработать его дважды."""
        if update.get("update_id") is not None:
            return f"uid:{update['update_id']}"

        # У callback свой ID. Проверяем его до ID исходного сообщения,
        # поскольку несколько нажатий могут относиться к одной клавиатуре.
        callback = update.get("callback") or {}
        callback_id = callback.get("callback_id")
        if callback_id is not None:
            return f"callback:{callback_id}"

        message = update.get("message") or {}
        body = message.get("body") or {}
        mid = body.get("mid") or body.get("message_id")
        if mid is not None:
            return f"mid:{mid}"

        sender = message.get("sender") or update.get("user") or {}
        text = body.get("text", "")
        ts = update.get("timestamp") or message.get("timestamp")
        return f"fallback:{sender.get('user_id')}:{ts}:{text}"

    def run(self):

        print("=" * 50)
        print("LifeCheck запущен")
        print("=" * 50)

        while True:

            try:

                response = self.api.get_updates(
                    marker=self.marker
                )

                if response.status_code != 200:
                    print("Ошибка:", response.status_code)
                    print(response.text)
                    time.sleep(2)
                    continue

                data = response.json()

                new_marker = data.get("marker")
                if new_marker is not None:
                    self.marker = new_marker

                updates = data.get("updates") or []

                for update in updates:

                    update_id = self._make_update_id(update)

                    if update_id in self.processed_ids:
                        print("Пропуск дубля:", update_id)
                        continue

                    self.processed_ids.add(update_id)

                    if len(self.processed_ids) > 1000:
                        self.processed_ids = set(
                            list(self.processed_ids)[-500:]
                        )

                    self.dispatcher.process(self.api, update)

                if not updates:
                    time.sleep(0.3)

            except KeyboardInterrupt:
                print("\nLifeCheck остановлен.")
                break

            except Exception as e:
                print("Ошибка:", e)
                time.sleep(2)
