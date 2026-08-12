from app.commands import day
from app.commands import menu

from database.repositories.users import users
from database.repositories.day_items import day_items


def handle(api, chat_id, user_id, first_name, text, screen=None):

    if text == "0":

        users.set_screen(user_id, "menu")
        menu.execute(api, chat_id, first_name)
        return True

    items = day_items.get_items(user_id)

    if text.isdigit():

        number = int(text)

        if 1 <= number <= len(items):

            day_items.toggle(
                user_id,
                items[number - 1]["code"]
            )

            day.execute(
                api,
                chat_id,
                user_id
            )

            return True

    api.send_message(
        chat_id=chat_id,
        text="Введите корректный номер."
    )

    return True