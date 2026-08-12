from app.commands import today
from app.commands import menu

from database.repositories.users import users
from database.repositories.habit_logs import habit_logs
from database.repositories.habits import habits as habits_repository
from database.repositories.water_logs import water_logs
from database.repositories.toilet_logs import toilet_logs
from database.repositories.sleep_logs import sleep_logs
from database.repositories.work_logs import work_logs
from database.repositories.migraine_logs import migraine_logs


def handle(
    api,
    chat_id,
    user_id,
    first_name,
    text
):

    text = text.strip()

    # ==================================================
    # НАЗАД
    # ==================================================

    if text == "0":

        users.set_screen(
            user_id,
            "menu"
        )

        menu.execute(
            api,
            chat_id,
            first_name
        )

        return

    # ==================================================
    # ТУАЛЕТ — ВЫБОР ТИПА СТУЛА
    # ==================================================

    if users.get_screen(user_id) == "toilet_type":

        stool_types = {
            "1": "жидко",
            "2": "мягко",
            "3": "нормально",
            "4": "запор"
        }

        if text == "0":

            users.set_screen(
                user_id,
                "today"
            )

            today.execute(
                api,
                chat_id,
                user_id
            )

            return

        stool_type = stool_types.get(
            text
        )

        if stool_type is None:

            api.send_message(
                chat_id=chat_id,
                text=(
                    "🚻 <b>Какой стул?</b>\n\n"
                    "1 — жидко\n"
                    "2 — мягко\n"
                    "3 — нормально\n"
                    "4 — запор\n\n"
                    "0 — отмена"
                )
            )

            return

        toilet_logs.add_visit(
            user_id,
            stool_type
        )

        users.set_screen(
            user_id,
            "today"
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # МИГРЕНЬ — ВВОД СИЛЫ
    # ==================================================

    if users.get_screen(user_id) == "migraine_intensity":

        if text == "0":

            users.set_screen(
                user_id,
                "today"
            )

            today.execute(
                api,
                chat_id,
                user_id
            )

            return

        if not text.isdigit():

            api.send_message(
                chat_id=chat_id,
                text=(
                    "🧠 Введите число "
                    "от <b>1 до 10</b>."
                )
            )

            return

        intensity = int(text)

        if intensity < 1 or intensity > 10:

            api.send_message(
                chat_id=chat_id,
                text=(
                    "🧠 Значение должно быть "
                    "от <b>1 до 10</b>."
                )
            )

            return

        migraine_logs.add_migraine(
            user_id,
            intensity
        )

        users.set_screen(
            user_id,
            "today"
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # ВОДА — ДОБАВИТЬ
    # ==================================================

    if text == "+":

        water_logs.add_glass(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # ВОДА — УБРАТЬ
    # ==================================================

    if text == "-":

        water_logs.remove_glass(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # ТУАЛЕТ — НОВОЕ ПОСЕЩЕНИЕ
    # ==================================================

    if text.lower() == "т+":

        users.set_screen(
            user_id,
            "toilet_type"
        )

        api.send_message(
            chat_id=chat_id,
            text=(
                "🚻 <b>Какой стул?</b>\n\n"
                "1 — жидко\n"
                "2 — мягко\n"
                "3 — нормально\n"
                "4 — запор\n\n"
                "0 — отмена"
            )
        )

        return

    # ==================================================
    # ТУАЛЕТ — УДАЛИТЬ ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ
    # ==================================================

    if text.lower() == "т-":

        toilet_logs.remove_visit(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # СОН — НАЧАТЬ
    # ==================================================

    if text.lower() == "сон":

        sleep_logs.start_sleep(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # СОН — ПРОБУЖДЕНИЕ
    # ==================================================

    if text.lower() == "пробуждение":

        sleep_logs.wake_up(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # РАБОТА — НАЧАТЬ
    # ==================================================

    if text.lower() == "работа":

        work_logs.start_work(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # РАБОТА — ЗАКОНЧИТЬ
    # ==================================================

    if text.lower() == "закончить работу":

        work_logs.finish_work(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # МИГРЕНЬ — ОТМЕТИТЬ
    # ==================================================

    if text.lower() == "мигрень+":

        users.set_screen(
            user_id,
            "migraine_intensity"
        )

        api.send_message(
            chat_id=chat_id,
            text=(
                "🧠 <b>Мигрень</b>\n\n"
                "Насколько сильно?\n\n"
                "Введите число от <b>1 до 10</b>.\n\n"
                "1 — очень слабо\n"
                "10 — очень сильно"
            )
        )

        return

    # ==================================================
    # МИГРЕНЬ — УБРАТЬ
    # ==================================================

    if text.lower() == "мигрень-":

        migraine_logs.remove_today(
            user_id
        )

        today.execute(
            api,
            chat_id,
            user_id
        )

        return

    # ==================================================
    # ПРИВЫЧКИ
    # ==================================================

    habits_list = habits_repository.get_habits(
        user_id
    )

    if text.isdigit():

        number = int(text)

        if 1 <= number <= len(habits_list):

            habit = habits_list[
                number - 1
            ]

            habit_logs.toggle_today(
                habit[0]
            )

            today.execute(
                api,
                chat_id,
                user_id
            )

            return

    # ==================================================
    # НЕПРАВИЛЬНАЯ КОМАНДА
    # ==================================================

    api.send_message(
        chat_id=chat_id,
        text=(
            "Не понял команду.\n\n"
            "В разделе «Сегодня» можно:\n"
            "+ — добавить стакан воды\n"
            "- — убрать стакан\n"
            "т+ — отметить туалет\n"
            "т- — убрать последнее посещение\n"
            "сон — начать сон\n"
            "пробуждение — проснуться\n"
            "работа — начать работу\n"
            "закончить работу — закончить работу\n"
            "мигрень+ — отметить мигрень\n"
            "мигрень- — убрать мигрень\n"
            "0 — назад"
        )
    )