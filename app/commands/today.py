from database.repositories.habits import habits
from database.repositories.habit_logs import habit_logs
from database.repositories.water_logs import water_logs
from database.repositories.toilet_logs import toilet_logs
from database.repositories.sleep_logs import sleep_logs
from database.repositories.work_logs import work_logs
from database.repositories.migraine_logs import migraine_logs
from database.repositories.blood_pressure_logs import blood_pressure_logs


def get_icon(title):

    title = title.lower()

    icons = {

        "🙏": [
            "молит",
            "правило",
            "евангел",
            "псалтир",
            "церков",
            "причаст",
            "исповед"
        ],

        "💧": [
            "вода",
            "пить"
        ],

        "💪": [
            "заряд",
            "спорт",
            "бег",
            "турник",
            "ходьба",
            "прогул"
        ],

        "📖": [
            "книга",
            "читать",
            "чтение"
        ],

        "💼": [
            "работ",
            "офис"
        ],

        "🚻": [
            "туалет"
        ],

        "🛏": [
            "сон",
            "спать"
        ],

        "🍎": [
            "еда",
            "завтрак",
            "обед",
            "ужин"
        ],

        "🎓": [
            "англий",
            "учеб",
            "урок"
        ]
    }

    for icon, words in icons.items():

        for word in words:

            if word in title:

                return icon

    return "⭐"


def progress_bar(done, total):

    if total == 0:

        return "□□□□□□□□□□"

    filled = int(
        (done / total) * 10
    )

    return (
        "■" * filled
        + "□" * (10 - filled)
    )


def water_progress_bar(count, goal):

    if goal <= 0:

        return "░░░░░░░░░░"

    progress = min(
        count / goal,
        1
    )

    filled = int(
        progress * 10
    )

    return (
        "█" * filled
        + "░" * (10 - filled)
    )


def execute(api, chat_id, user_id):

    habits_list = habits.get_habits(
        user_id
    )

    # =================================================
    # ВОДА
    # =================================================

    water_count = water_logs.get_today_count(
        user_id
    )

    water_last_time = (
        water_logs.get_last_time_today(
            user_id
        )
    )

    # =================================================
    # ТУАЛЕТ
    # =================================================

    toilet_count = toilet_logs.get_today_count(
        user_id
    )

    toilet_last_time = (
        toilet_logs.get_last_time_today(
            user_id
        )
    )

    toilet_visits = (
        toilet_logs.get_today_visits(
            user_id
        )
    )

    # =================================================
    # СОН
    # =================================================

    sleep_info = sleep_logs.get_today_info(
        user_id
    )

    sleep_started = sleep_info["started"]
    sleep_wake_up = sleep_info["wake_up"]
    sleep_duration = sleep_info["duration"]

    # =================================================
    # РАБОТА
    # =================================================

    work_info = work_logs.get_today_info(
        user_id
    )

    work_started = work_info["started"]
    work_finished = work_info["finished"]
    work_duration = work_info["duration"]

    # =================================================
    # МИГРЕНЬ
    # =================================================

    migraine_info = migraine_logs.get_today_info(
        user_id
    )

    migraine_exists = migraine_info["exists"]
    migraine_intensity = migraine_info["intensity"]
    migraine_time = migraine_info["time"]

    # =================================================
    # ДАВЛЕНИЕ
    # =================================================

    blood_pressure_measurements = (
        blood_pressure_logs.get_today_measurements(
            user_id
        )
    )

    blood_pressure_count = (
        blood_pressure_logs.get_today_count(
            user_id
        )
    )

    # =================================================
    # Заголовок
    # =================================================

    text = (
        "☀️ <b>Сегодня</b>\n\n"
    )

    # =================================================
    # ВОДА
    # =================================================

    text += (
        "💧 <b>Вода</b>\n\n"
    )

    water_goal = water_logs.DAILY_GOAL

    water_bar = water_progress_bar(
        water_count,
        water_goal
    )

    text += (
        f"{water_bar}  "
        f"{water_count} / {water_goal}\n"
    )

    if water_last_time:

        text += (
            f"🕐 Последний стакан: "
            f"{water_last_time}\n"
        )

    text += (
        "\n"
        "➕ + стакан\n"
        "➖ − стакан\n\n"
    )

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    # =================================================
    # ТУАЛЕТ
    # =================================================

    text += (
        "🚻 <b>Туалет</b>\n\n"
    )

    text += (
        f"Сегодня: "
        f"<b>{toilet_count}</b> раз\n"
    )

    # =================================================
    # Список посещений сегодня
    # =================================================

    if toilet_visits:

        text += "\n"

        stool_names = {
            "жидко": "жидко",
            "мягко": "мягко",
            "нормально": "нормально",
            "запор": "запор"
        }

        for visit in toilet_visits:

            visit_time = visit.get(
                "time"
            )

            stool_type = visit.get(
                "stool_type"
            )

            if not stool_type:

                stool_text = "тип не указан"

            else:

                stool_text = stool_names.get(
                    stool_type,
                    stool_type
                )

            if visit_time:

                text += (
                    f"🕐 {visit_time} — "
                    f"{stool_text}\n"
                )

            else:

                text += (
                    "🕐 --:-- — "
                    f"{stool_text}\n"
                )

    elif toilet_last_time:

        text += (
            f"\n🕐 Последний: "
            f"{toilet_last_time}\n"
        )

    text += (
        "\n"
        "т+ — отметить\n"
        "т− — убрать\n\n"
    )

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    # =================================================
    # ДАВЛЕНИЕ
    # =================================================

    text += (
        "🩺 <b>Давление</b>\n\n"
    )

    if blood_pressure_count == 0:

        text += (
            "Сегодня измерений нет.\n"
        )

    else:

        text += (
            f"Измерений сегодня: "
            f"<b>{blood_pressure_count}</b>\n\n"
        )

        for measurement in (
            blood_pressure_measurements
        ):

            measurement_time = (
                measurement.get("time")
            )

            systolic = (
                measurement.get("systolic")
            )

            diastolic = (
                measurement.get("diastolic")
            )

            pulse = (
                measurement.get("pulse")
            )

            if not measurement_time:

                measurement_time = "--:--"

            text += (
                f"🕐 {measurement_time} — "
                f"<b>{systolic}/{diastolic}</b>"
            )

            if pulse is not None:

                text += (
                    f", пульс {pulse}"
                )

            text += "\n"

    text += (
        "\n"
        "4 → Здоровье → 1 — новое измерение\n\n"
    )

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    # =================================================
    # СОН
    # =================================================

    text += (
        "😴 <b>Сон</b>\n\n"
    )

    if sleep_started:

        text += (
            f"🌙 Лёг спать: "
            f"{sleep_started.strftime('%H:%M')}\n"
        )

    if sleep_wake_up:

        text += (
            f"☀️ Проснулся: "
            f"{sleep_wake_up.strftime('%H:%M')}\n"
        )

    if sleep_duration:

        text += (
            f"⏱ Продолжительность: "
            f"<b>{sleep_duration}</b>\n"
        )

    if sleep_started and not sleep_wake_up:

        text += (
            "\n"
            "☀️ пробуждение\n"
        )

    elif not sleep_started:

        text += (
            "🌙 сон — начать\n"
        )

    text += "\n"

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    # =================================================
    # РАБОТА
    # =================================================

    text += (
        "💼 <b>Работа</b>\n\n"
    )

    if work_started:

        text += (
            f"🟢 Начал: "
            f"{work_started.strftime('%H:%M')}\n"
        )

    if work_finished:

        text += (
            f"🔴 Закончил: "
            f"{work_finished.strftime('%H:%M')}\n"
        )

    if work_duration:

        text += (
            f"⏱ Продолжительность: "
            f"<b>{work_duration}</b>\n"
        )

    if work_started and not work_finished:

        text += (
            "\n"
            "⏹ закончить работу\n"
        )

    elif not work_started:

        text += (
            "▶️ начать работу\n"
        )

    text += "\n"

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    # =================================================
    # МИГРЕНЬ
    # =================================================

    text += (
        "🧠 <b>Мигрень</b>\n\n"
    )

    if migraine_exists:

        text += (
            "Сегодня: <b>да</b>\n"
            f"Сила: "
            f"<b>{migraine_intensity} / 10</b>\n"
        )

        if migraine_time:

            text += (
                f"🕐 Отмечено: "
                f"{migraine_time}\n"
            )

        text += (
            "\n"
            "мигрень- — убрать\n"
        )

    else:

        text += (
            "Сегодня: <b>нет</b>\n\n"
            "мигрень+ — отметить\n"
        )

    text += "\n"

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    # =================================================
    # ПРИВЫЧКИ
    # =================================================

    if not habits_list:

        text += (
            "⭐ <b>Привычки</b>\n\n"
            "Пока нет ни одной привычки.\n"
            "Добавьте первую в разделе "
            "«Привычки».\n\n"
        )

        text += (
            "━━━━━━━━━━━━━━\n\n"
        )

        text += (
            "Введите номер привычки.\n"
            "0 — назад."
        )

        api.send_message(
            chat_id=chat_id,
            text=text
        )

        return

    completed = 0

    total = len(
        habits_list
    )

    text += (
        "⭐ <b>Привычки</b>\n\n"
    )

    # =================================================
    # Список привычек
    # =================================================

    for number, habit in enumerate(
        habits_list,
        start=1
    ):

        habit_id = habit[0]
        title = habit[1]

        icon = get_icon(
            title
        )

        done = (
            habit_logs.is_completed_today(
                habit_id
            )
        )

        completed_time = None

        if done:

            completed += 1

            completed_time = (
                habit_logs
                .get_completed_time_today(
                    habit_id
                )
            )

        mark = (
            "☑"
            if done
            else "☐"
        )

        if completed_time:

            time_text = (
                f"   🕐 {completed_time}"
            )

        else:

            time_text = ""

        text += (
            f"{number}. "
            f"{mark} "
            f"{icon} "
            f"{title}"
            f"{time_text}\n\n"
        )

    # =================================================
    # Прогресс привычек
    # =================================================

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    text += (
        "📈 <b>Прогресс привычек</b>\n\n"
    )

    text += progress_bar(
        completed,
        total
    )

    text += (
        "\n\n"
        f"<b>{completed} из {total}</b>\n\n"
    )

    text += (
        "━━━━━━━━━━━━━━\n\n"
    )

    text += (
        "Введите номер привычки.\n"
        "0 — назад."
    )

    api.send_message(
        chat_id=chat_id,
        text=text
    )