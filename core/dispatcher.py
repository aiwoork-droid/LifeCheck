from app.dispatcher import dispatcher
from database.repositories.users import users


class Dispatcher:

    def process(self, api, update):

        print()
        print("=" * 60)
        print("CORE DISPATCHER: получено обновление")

        update_type = update.get("update_type")
        print("UPDATE TYPE:", update_type)

        is_main_menu_callback = False

        # Обычное сообщение, введённое пользователем.
        if update_type == "message_created":
            message = update.get("message") or {}
            sender = message.get("sender") or {}

            # Не отвечаем на сообщения самого бота.
            if sender.get("is_bot") is True:
                print("Сообщение от бота — пропускаем.")
                print("=" * 60)
                return

            text = (message.get("body") or {}).get("text", "")

        # Нажатие inline-кнопки MAX.
        elif update_type == "message_callback":
            callback = update.get("callback") or {}
            callback_id = callback.get("callback_id")
            sender = callback.get("user") or {}
            payload = callback.get("payload")
            message = update.get("message")

            # Подтверждаем callback. Ошибка подтверждения не блокирует
            # обработку самого действия пользователя.
            if callback_id and hasattr(api, "answer_callback"):
                try:
                    response = api.answer_callback(callback_id)
                    if response is not None and response.status_code >= 400:
                        print(
                            "Не удалось подтвердить callback:",
                            response.status_code,
                            response.text
                        )
                except Exception as exc:
                    print("Ошибка подтверждения callback:", exc)

            if not isinstance(message, dict):
                print("В callback нет исходного сообщения — пропускаем.")
                print("=" * 60)
                return

            if payload is None:
                print("В callback нет payload — пропускаем.")
                print("=" * 60)
                return

            message = dict(message)
            message["sender"] = sender
            body = dict(message.get("body") or {})
            text = str(payload)

            # Главные кнопки всегда открывают соответствующий пункт
            # главного меню, даже если нажали старое сообщение с меню.
            if text.startswith("main:"):
                destination = text.partition(":")[2]
                if destination not in {"1", "2", "3", "4", "5", "6"}:
                    print("Неизвестный payload главного меню:", repr(text))
                    print("=" * 60)
                    return
                text = destination
                is_main_menu_callback = True

            body["text"] = text
            message["body"] = body
            print("CALLBACK PAYLOAD:", repr(payload))

        else:
            print("Это не message_created и не message_callback. Пропускаем.")
            print("=" * 60)
            return

        user_id = sender.get("user_id")
        if user_id is None:
            print("Нет user_id — пропускаем.")
            print("=" * 60)
            return

        print("USER ID:", user_id)
        print("TEXT:", repr(text))

        if not users.user_exists(user_id):
            print("Пользователь новый. Создаём.")
            users.create_user(
                user_id=user_id,
                first_name=sender.get("first_name", ""),
                last_name=sender.get("last_name", "")
            )
        else:
            print("Пользователь уже существует.")

        users.update_activity(user_id)

        if is_main_menu_callback:
            users.set_screen(user_id, "menu")
            screen = "menu"
        else:
            screen = users.get_screen(user_id)

        print("CURRENT SCREEN:", screen)
        print("Передаём сообщение в app.dispatcher...")

        dispatcher.dispatch(
            api,
            message,
            screen
        )

        print("APP DISPATCHER: обработка завершена")
        print("=" * 60)
