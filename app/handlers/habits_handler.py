from app.commands import today
from app.commands import menu
from app.commands import habits

from database.repositories.users import users
from database.repositories.habits import habits as habits_repository
from database.repositories.habit_logs import habit_logs


def handle(api, chat_id, user_id, first_name, text, screen=None):

    # ==================================================
    # МЕНЮ ПРИВЫЧЕК
    # ==================================================

    if screen == "habits":

        # Назад
        if text == "0":

            users.set_screen(user_id, "menu")

            menu.execute(
                api,
                chat_id,
                first_name
            )

            return True

        # Добавить привычку
        if text == "1":

            users.set_screen(
                user_id,
                "add_habit"
            )

            api.send_message(
                chat_id=chat_id,
                text=(
                    "➕ <b>Новая привычка</b>\n\n"
                    "Напишите название привычки.\n\n"
                    "Например:\n"
                    "💧 Пить воду\n"
                    "💪 Зарядка\n"
                    "📖 Читать книгу\n\n"
                    "0. 🔙 Назад"
                )
            )

            return True

        # Список привычек
        if text == "2":

            habits_list = habits_repository.get_habits(
                user_id
            )

            if not habits_list:

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "📋 <b>Мои привычки</b>\n\n"
                        "Пока нет ни одной привычки.\n\n"
                        "Добавьте первую 😊"
                    )
                )

                return True

            result = "📋 <b>Мои привычки</b>\n\n"

            for number, habit in enumerate(
                habits_list,
                start=1
            ):

                result += (
                    f"{number}. ⭐ {habit[1]}\n"
                )

            result += "\n0. 🔙 Назад"

            api.send_message(
                chat_id=chat_id,
                text=result
            )

            return True

        # Удалить привычку
        if text == "3":

            habits_list = habits_repository.get_habits(
                user_id
            )

            if not habits_list:

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "❌ <b>Удаление привычки</b>\n\n"
                        "У вас пока нет привычек."
                    )
                )

                return True

            users.set_screen(
                user_id,
                "delete_habit"
            )

            result = (
                "❌ <b>Удалить привычку</b>\n\n"
                "Введите номер привычки:\n\n"
            )

            for number, habit in enumerate(
                habits_list,
                start=1
            ):

                result += (
                    f"{number}. {habit[1]}\n"
                )

            result += "\n0. 🔙 Назад"

            api.send_message(
                chat_id=chat_id,
                text=result
            )

            return True

        api.send_message(
            chat_id=chat_id,
            text="Выберите пункт меню."
        )

        return True

    # ==================================================
    # ДОБАВЛЕНИЕ ПРИВЫЧКИ
    # ==================================================

    if screen == "add_habit":

        # Назад
        if text == "0":

            users.set_screen(
                user_id,
                "habits"
            )

            habits.execute(
                api,
                chat_id
            )

            return True

        # Пустой текст
        if not text:

            api.send_message(
                chat_id=chat_id,
                text=(
                    "Название привычки не может быть пустым.\n\n"
                    "Напишите название или 0 — назад."
                )
            )

            return True

        # Проверяем дубликат
        if habits_repository.habit_exists(
            user_id,
            text
        ):

            api.send_message(
                chat_id=chat_id,
                text=(
                    "⚠️ Такая привычка уже существует.\n\n"
                    "Введите другое название."
                )
            )

            return True

        # Добавляем
        habits_repository.add_habit(
            user_id,
            text
        )

        api.send_message(
            chat_id=chat_id,
            text=(
                f"✅ Привычка «{text}» добавлена!"
            )
        )

        users.set_screen(
            user_id,
            "habits"
        )

        habits.execute(
            api,
            chat_id
        )

        return True

    # ==================================================
    # УДАЛЕНИЕ ПРИВЫЧКИ
    # ==================================================

    if screen == "delete_habit":

        # Назад
        if text == "0":

            users.set_screen(
                user_id,
                "habits"
            )

            habits.execute(
                api,
                chat_id
            )

            return True

        habits_list = habits_repository.get_habits(
            user_id
        )

        if text.isdigit():

            number = int(text)

            if 1 <= number <= len(habits_list):

                habit = habits_list[number - 1]

                habit_id = habit[0]
                title = habit[1]

                # Удаляем привычку
                habits_repository.delete_habit(
                    habit_id
                )

                # Удаляем историю выполнения
                try:

                    habit_logs.db.cursor.execute(
                        """
                        DELETE FROM habit_logs
                        WHERE habit_id=?
                        """,
                        (habit_id,)
                    )

                    habit_logs.db.connection.commit()

                except Exception:

                    pass

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🗑 Привычка «{title}» удалена."
                    )
                )

                users.set_screen(
                    user_id,
                    "habits"
                )

                habits.execute(
                    api,
                    chat_id
                )

                return True

        api.send_message(
            chat_id=chat_id,
            text=(
                "Введите корректный номер привычки."
            )
        )

        return True

    # ==================================================
    # НЕИЗВЕСТНЫЙ ЭКРАН
    # ==================================================

    api.send_message(
        chat_id=chat_id,
        text="Не удалось определить раздел."
    )

    return True