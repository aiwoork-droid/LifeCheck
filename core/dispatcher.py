from app.dispatcher import dispatcher
from database.repositories.users import users


class Dispatcher:

    def process(self, api, update):

        print()
        print("=" * 60)
        print("CORE DISPATCHER: получено обновление")
        print("UPDATE:", update)

        if update.get("update_type") != "message_created":
            print("Это не message_created. Пропускаем.")
            print("=" * 60)
            return

        message = update["message"]

        print("MESSAGE:", message)

        sender = message["sender"]

        user_id = sender["user_id"]

        print("USER ID:", user_id)

        # Создаём пользователя при первом сообщении
        if not users.user_exists(user_id):

            print("Пользователь новый. Создаём.")

            users.create_user(
                user_id=user_id,
                first_name=sender.get("first_name", ""),
                last_name=sender.get("last_name", "")
            )

        else:

            print("Пользователь уже существует.")

        # Обновляем активность
        users.update_activity(user_id)

        print("Активность пользователя обновлена.")

        # Получаем текущий экран
        screen = users.get_screen(user_id)

        print("CURRENT SCREEN:", screen)

        # Передаём сообщение в основной dispatcher
        print("Передаём сообщение в app.dispatcher...")

        dispatcher.dispatch(
            api,
            message,
            screen
        )

        print("APP DISPATCHER: обработка завершена")
        print("=" * 60)