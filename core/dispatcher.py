from app.dispatcher import dispatcher
from database.repositories.users import users


class Dispatcher:

    def process(self, api, update):

        if update.get("update_type") != "message_created":
            return

        message = update["message"]

        sender = message["sender"]

        user_id = sender["user_id"]

        # создаем пользователя при первом сообщении
        if not users.user_exists(user_id):

            users.create_user(
                user_id=user_id,
                first_name=sender.get("first_name", ""),
                last_name=sender.get("last_name", "")
            )

        users.update_activity(user_id)

        screen = users.get_screen(user_id)

        dispatcher.dispatch(
            api,
            message,
            screen
        )