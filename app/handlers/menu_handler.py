from app.commands import menu
from app.commands import today
from app.commands import habits
from app.commands import day

from database.repositories.users import users


def handle(
    api,
    chat_id,
    user_id,
    first_name,
    text
):

    # ==========================================
    # Сегодня
    # ==========================================

    if text == "1":

        users.set_screen(
            user_id,
            "today"
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return True

    # ==========================================
    # Мой день
    # ==========================================

    elif text == "2":

        users.set_screen(
            user_id,
            "day"
        )

        day.execute(
            api,
            chat_id,
            user_id
        )

        return True

    # ==========================================
    # Привычки
    # ==========================================

    elif text == "3":

        users.set_screen(
            user_id,
            "habits"
        )

        habits.execute(
            api,
            chat_id
        )

        return True

    # ==========================================
    # Здоровье
    # ==========================================

    elif text == "4":

        users.set_screen(
            user_id,
            "health"
        )

        api.send_message(
            chat_id=chat_id,
            text=(
                "❤️ <b>Здоровье</b>\n\n"
                "1 — 🩺 Давление\n"
                "2 — 🧠 Мигрень\n\n"
                "0 — назад"
            )
        )

        return True

    # ==========================================
    # Статистика
    # ==========================================

    elif text == "5":

        users.set_screen(
            user_id,
            "statistics"
        )

        api.send_message(
            chat_id=chat_id,
            text=(
                "📊 <b>Статистика</b>\n\n"
                "1 — Сегодня\n"
                "2 — Неделя\n"
                "3 — Месяц\n"
                "4 — Год\n\n"
                "0 — назад"
            )
        )

        return True

    # ==========================================
    # Настройки
    # ==========================================

    elif text == "6":

        api.send_message(
            chat_id=chat_id,
            text=(
                "⚙️ Настройки пока находятся "
                "в разработке."
            )
        )

        return True

    # ==========================================
    # Неизвестная команда
    # ==========================================

    api.send_message(
        chat_id=chat_id,
        text="Выберите пункт меню."
    )

    return True


menu_handler = handle