from database.repository import repository
from app.commands import menu


def execute(api, message):

    sender = message["sender"]

    user_id = sender["user_id"]
    first_name = sender.get("first_name", "")
    last_name = sender.get("last_name", "")

    chat_id = message["recipient"]["chat_id"]

    if not repository.user_exists(user_id):

        repository.create_user(
            user_id,
            first_name,
            last_name
        )

        print(f"✅ Новый пользователь: {first_name}")

    else:

        repository.update_activity(user_id)

    menu.execute(
        api,
        chat_id,
        first_name
    )