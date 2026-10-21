from datetime import date, datetime, timedelta
import calendar

from database.db import Database

db = Database()

WEEKDAYS = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье"
]

MONTHS = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь"
]

STOOL_TYPES = {
    "жидко": "жидко",
    "мягко": "мягко",
    "нормально": "нормально",
    "запор": "запор"
}


# ==================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==================================================

def format_date(value):

    return value.strftime("%d.%m.%Y")


def format_time(value):

    if not value:
        return None

    try:

        return datetime.fromisoformat(
            value
        ).strftime("%H:%M")

    except Exception:

        return None


# ==================================================
# ВОДА
# ==================================================

def get_water(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            log_date,
            COUNT(*)
        FROM water_logs
        WHERE
            user_id = ?
            AND log_date BETWEEN ? AND ?
        GROUP BY log_date
        ORDER BY log_date
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    return {
        row[0]: int(row[1] or 0)
        for row in db.cursor.fetchall()
    }


# ==================================================
# ТУАЛЕТ
# ==================================================

def get_toilet(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            log_date,
            stool_type,
            created_at
        FROM toilet_logs
        WHERE
            user_id = ?
            AND log_date BETWEEN ? AND ?
        ORDER BY log_date, id
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    result = {}

    for log_date, stool_type, created_at in db.cursor.fetchall():

        if log_date not in result:

            result[log_date] = []

        result[log_date].append(
            {
                "type": stool_type,
                "time": format_time(created_at)
            }
        )

    return result


# ==================================================
# ДЛИТЕЛЬНОСТЬ
# ==================================================

def calc_duration(started_iso, end_iso):
    if not started_iso or not end_iso:
        return None
    try:
        t1 = datetime.fromisoformat(started_iso)
        t2 = datetime.fromisoformat(end_iso)
        total_minutes = int((t2 - t1).total_seconds() / 60)
        if total_minutes < 0:
            return None
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours} ч {minutes} мин"
    except Exception:
        return None


# ==================================================
# СОН
# ==================================================

def get_sleep(user_id, start_date, end_date):

    # Для одного дня берём ещё и вчера
    # (лёг вечером — проснулся утром)
    query_start = start_date
    if start_date == end_date:
        query_start = start_date - timedelta(days=1)

    db.cursor.execute(
        """
        SELECT
            sleep_date,
            sleep_started_at,
            wake_up_at
        FROM sleep_logs
        WHERE
            user_id = ?
            AND sleep_date BETWEEN ? AND ?
        ORDER BY sleep_date, id
        """,
        (
            user_id,
            query_start.isoformat(),
            end_date.isoformat()
        )
    )

    result = {}

    for sleep_date, started, wake_up in db.cursor.fetchall():

        key = sleep_date

        # Вчерашний сон, который закончился сегодня —
        # показываем в сегодняшнем отчёте
        if start_date == end_date and sleep_date != end_date.isoformat():
            if wake_up:
                try:
                    wake_dt = datetime.fromisoformat(wake_up)
                    if wake_dt.date() == end_date:
                        key = end_date.isoformat()
                    else:
                        continue
                except Exception:
                    continue
            else:
                # незакрытый вчерашний — тоже показываем сегодня
                key = end_date.isoformat()

        result[key] = {
            "started": format_time(started),
            "wake_up": format_time(wake_up),
            "duration": calc_duration(started, wake_up)
        }

    return result


# ==================================================
# РАБОТА
# ==================================================

def get_work(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            work_date,
            work_started_at,
            work_finished_at
        FROM work_logs
        WHERE
            user_id = ?
            AND work_date BETWEEN ? AND ?
        ORDER BY work_date, id
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    result = {}

    for work_date, started, finished in db.cursor.fetchall():

        result[work_date] = {
            "started": format_time(started),
            "finished": format_time(finished),
            "duration": calc_duration(started, finished)
        }

    return result


# ==================================================
# МИГРЕНЬ
# ==================================================

def get_migraine(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            migraine_date,
            intensity,
            created_at
        FROM migraine_logs
        WHERE
            user_id = ?
            AND migraine_date BETWEEN ? AND ?
        ORDER BY migraine_date
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    result = {}

    for migraine_date, intensity, created_at in db.cursor.fetchall():

        result[migraine_date] = {
            "intensity": intensity,
            "time": format_time(created_at)
        }

    return result


# ==================================================
# ПРИВЫЧКИ
# ==================================================

def get_habits(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            hl.log_date,
            h.title,
            hl.completed,
            hl.completed_at
        FROM habit_logs hl
        JOIN habits h
            ON h.id = hl.habit_id
        WHERE
            h.user_id = ?
            AND hl.log_date BETWEEN ? AND ?
            AND hl.completed = 1
        ORDER BY hl.log_date, h.id
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    result = {}

    for log_date, title, completed, completed_at in db.cursor.fetchall():

        if log_date not in result:

            result[log_date] = []

        result[log_date].append(
            {
                "title": title,
                "time": format_time(completed_at)
            }
        )

    return result


# ==================================================
# ДАВЛЕНИЕ
# ==================================================

def get_blood_pressure(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            log_date,
            systolic,
            diastolic,
            pulse,
            created_at
        FROM blood_pressure_logs
        WHERE
            user_id = ?
            AND log_date BETWEEN ? AND ?
        ORDER BY log_date, id
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    result = {}

    for (
        log_date,
        systolic,
        diastolic,
        pulse,
        created_at
    ) in db.cursor.fetchall():

        if log_date not in result:

            result[log_date] = []

        result[log_date].append(
            {
                "systolic": systolic,
                "diastolic": diastolic,
                "pulse": pulse,
                "time": format_time(created_at)
            }
        )

    return result


# ==================================================
# ФОРМАТИРОВАНИЕ ДАВЛЕНИЯ
# ==================================================


def get_blood_sugar(user_id, start_date, end_date):

    db.cursor.execute(
        """
        SELECT
            log_date,
            value,
            meal_context,
            created_at
        FROM blood_sugar_logs
        WHERE
            user_id = ?
            AND log_date BETWEEN ? AND ?
        ORDER BY log_date, id
        """,
        (
            user_id,
            start_date.isoformat(),
            end_date.isoformat()
        )
    )

    meal_labels = {
        "before": "до еды",
        "after": "после еды",
        "between": "между приёмами (2 ч)"
    }

    result = {}

    for log_date, value, meal_context, created_at in db.cursor.fetchall():

        if log_date not in result:
            result[log_date] = []

        result[log_date].append(
            {
                "value": value,
                "meal_context": meal_context,
                "meal_label": meal_labels.get(
                    meal_context,
                    meal_context or "—"
                ),
                "time": format_time(created_at)
            }
        )

    return result


def format_pressure(measurement):

    time_text = (
        measurement["time"]
        or "--:--"
    )

    systolic = measurement["systolic"]
    diastolic = measurement["diastolic"]
    pulse = measurement["pulse"]

    text = (
        f"{time_text} — "
        f"<b>{systolic}/{diastolic}</b>"
    )

    if pulse is not None:

        text += (
            f" • пульс {pulse}"
        )

    return text


# ==================================================
# ДНЕВНОЙ ОТЧЁТ
# ==================================================

def build_day_report(
    user_id,
    target_date
):

    water = get_water(
        user_id,
        target_date,
        target_date
    )

    toilet = get_toilet(
        user_id,
        target_date,
        target_date
    )

    sleep = get_sleep(
        user_id,
        target_date,
        target_date
    )

    work = get_work(
        user_id,
        target_date,
        target_date
    )

    migraine = get_migraine(
        user_id,
        target_date,
        target_date
    )

    habits = get_habits(
        user_id,
        target_date,
        target_date
    )

    blood_pressure = get_blood_pressure(
        user_id,
        target_date,
        target_date
    )

    blood_sugar = get_blood_sugar(
        user_id,
        target_date,
        target_date
    )

    key = target_date.isoformat()

    text = (
        f"📅 <b>{WEEKDAYS[target_date.weekday()]}, "
        f"{target_date.strftime('%d.%m.%Y')}</b>\n\n"
    )

    # ==================================================
    # ВОДА
    # ==================================================

    water_count = water.get(
        key,
        0
    )

    text += (
        "💧 <b>Вода</b>\n"
        f"{water_count} раз × 200 мл"
        f" = <b>{water_count * 200} мл</b>\n\n"
    )

    # ==================================================
    # ТУАЛЕТ
    # ==================================================

    text += "🚻 <b>Стул</b>\n"

    toilet_visits = toilet.get(
        key,
        []
    )

    if not toilet_visits:

        text += "Нет записей\n\n"

    else:

        text += (
            f"Всего: <b>{len(toilet_visits)}</b> раз\n"
        )

        for visit in toilet_visits:

            time_text = (
                visit["time"]
                or "--:--"
            )

            stool_type = (
                STOOL_TYPES.get(
                    visit["type"],
                    visit["type"]
                )
                if visit["type"]
                else "тип не указан"
            )

            text += (
                f"{time_text} — "
                f"{stool_type}\n"
            )

        text += "\n"

    # ==================================================
    # ДАВЛЕНИЕ
    # ==================================================

    text += "🩺 <b>Давление</b>\n"

    pressure_measurements = blood_pressure.get(
        key,
        []
    )

    if not pressure_measurements:

        text += (
            "Нет измерений\n\n"
        )

    else:

        for measurement in pressure_measurements:

            text += (
                format_pressure(
                    measurement
                )
                + "\n"
            )

        text += "\n"

    # ==================================================
    # САХАР
    # ==================================================

    text += "🩸 <b>Сахар</b>\n"

    sugar_measurements = blood_sugar.get(
        key,
        []
    )

    if not sugar_measurements:

        text += (
            "Нет измерений\n\n"
        )

    else:

        for measurement in sugar_measurements:

            time_text = (
                measurement["time"]
                or "--:--"
            )

            value = measurement["value"]
            label = measurement["meal_label"]

            text += (
                f"{time_text} — "
                f"<b>{value}</b> ммоль/л "
                f"({label})\n"
            )

        text += "\n"

    # ==================================================
    # МИГРЕНЬ
    # ==================================================

    text += "🧠 <b>Мигрень</b>\n"

    migraine_info = migraine.get(
        key
    )

    if migraine_info:

        text += (
            f"{migraine_info['time'] or '--:--'} — "
            f"{migraine_info['intensity']}/10\n\n"
        )

    else:

        text += "Нет\n\n"

    # ==================================================
    # САХАР
    # ==================================================

    text += "🩸 <b>Сахар</b>\n"

    sugar_count = 0

    current = first_day

    while current <= last_day:

        key = current.isoformat()
        measurements = blood_sugar.get(key, [])

        if measurements:
            text += f"\n<b>{current.strftime('%d.%m')}</b>\n"

            for measurement in measurements:
                time_text = measurement["time"] or "--:--"
                text += (
                    f"{time_text} — "
                    f"<b>{measurement['value']}</b> ммоль/л "
                    f"({measurement['meal_label']})\n"
                )
                sugar_count += 1

        current += timedelta(days=1)

    if sugar_count == 0:
        text += "Нет измерений\n"
    else:
        text += f"\nВсего измерений: <b>{sugar_count}</b>\n"

    text += "\n"

    # ==================================================
    # СОН
    # ==================================================

    text += "😴 <b>Сон</b>\n"

    sleep_info = sleep.get(key)

    if sleep_info:

        started = sleep_info["started"] or "--:--"
        wake_up = sleep_info["wake_up"] or "--:--"
        duration = sleep_info.get("duration")

        line = f"{started} — {wake_up}"
        if duration:
            line += f" ({duration})"

        text += line + "\n\n"

    else:

        text += "Нет записей\n\n"

    # ==================================================
    # РАБОТА
    # ==================================================

    text += "💼 <b>Работа</b>\n"

    work_info = work.get(key)

    if work_info:

        started = work_info["started"] or "--:--"
        finished = work_info["finished"] or "--:--"
        duration = work_info.get("duration")

        line = f"{started} — {finished}"
        if duration:
            line += f" ({duration})"

        text += line + "\n\n"

    else:

        text += "Нет записей\n\n"

    # ==================================================
    # ПРИВЫЧКИ
    # ==================================================

    text += "⭐ <b>Привычки</b>\n"

    habit_list = habits.get(
        key,
        []
    )

    if habit_list:

        for habit in habit_list:

            time_text = ""

            if habit["time"]:

                time_text = (
                    f" — {habit['time']}"
                )

            text += (
                f"☑ {habit['title']}"
                f"{time_text}\n"
            )

    else:

        text += "Нет выполненных\n"

    return text


# ==================================================
# НЕДЕЛЬНЫЙ ОТЧЁТ
# ==================================================

def build_week_report(
    user_id,
    target_date
):

    monday = (
        target_date
        - timedelta(
            days=target_date.weekday()
        )
    )

    sunday = monday + timedelta(
        days=6
    )

    water = get_water(
        user_id,
        monday,
        sunday
    )

    toilet = get_toilet(
        user_id,
        monday,
        sunday
    )

    migraine = get_migraine(
        user_id,
        monday,
        sunday
    )

    blood_pressure = get_blood_pressure(
        user_id,
        monday,
        sunday
    )

    sleep = get_sleep(
        user_id,
        monday,
        sunday
    )

    work = get_work(
        user_id,
        monday,
        sunday
    )

    blood_sugar = get_blood_sugar(
        user_id,
        monday,
        sunday
    )


    text = (
        f"📊 <b>Неделя</b>\n"
        f"{monday.strftime('%d.%m')} — "
        f"{sunday.strftime('%d.%m.%Y')}\n\n"
    )

    # ==================================================
    # ВОДА
    # ==================================================

    text += "💧 <b>Вода</b>\n"

    total_water = 0

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()

        count = water.get(
            key,
            0
        )

        total_water += count

        text += (
            f"{WEEKDAYS[i]} — "
            f"{count} × 200 мл\n"
        )

    text += (
        f"Итого: <b>{total_water * 200} мл</b>\n\n"
    )

    # ==================================================
    # СТУЛ
    # ==================================================

    text += "🚻 <b>Стул</b>\n"

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()

        visits = toilet.get(
            key,
            []
        )

        text += (
            f"\n<b>{WEEKDAYS[i]}</b>\n"
        )

        if not visits:

            text += "нет\n"

            continue

        for visit in visits:

            time_text = (
                visit["time"]
                or "--:--"
            )

            stool_type = (
                STOOL_TYPES.get(
                    visit["type"],
                    visit["type"]
                )
                if visit["type"]
                else "тип не указан"
            )

            text += (
                f"{time_text} — "
                f"{stool_type}\n"
            )

    text += "\n"

    # ==================================================
    # ДАВЛЕНИЕ
    # ==================================================

    text += "🩺 <b>Давление</b>\n"

    pressure_count = 0

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()

        measurements = blood_pressure.get(
            key,
            []
        )

        if not measurements:

            continue

        text += (
            f"\n<b>{WEEKDAYS[i]} "
            f"{current.strftime('%d.%m')}</b>\n"
        )

        for measurement in measurements:

            text += (
                format_pressure(
                    measurement
                )
                + "\n"
            )

            pressure_count += 1

    if pressure_count == 0:

        text += "Нет измерений\n"

    else:

        text += (
            f"\nВсего измерений: "
            f"<b>{pressure_count}</b>\n"
        )

    text += "\n"

    # ==================================================
    # СОН
    # ==================================================

    text += "😴 <b>Сон</b>\n"

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()

        info = sleep.get(key)

        if info:

            started = info["started"] or "--:--"
            wake_up = info["wake_up"] or "--:--"
            duration = info.get("duration")

            line = f"{WEEKDAYS[i]} — {started} — {wake_up}"
            if duration:
                line += f" ({duration})"

            text += line + "\n"

        else:

            text += (
                f"{WEEKDAYS[i]} — нет\n"
            )

    text += "\n"

    # ==================================================
    # РАБОТА
    # ==================================================

    text += "💼 <b>Работа</b>\n"

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()

        info = work.get(key)

        if info:

            started = info["started"] or "--:--"
            finished = info["finished"] or "--:--"
            duration = info.get("duration")

            line = f"{WEEKDAYS[i]} — {started} — {finished}"
            if duration:
                line += f" ({duration})"

            text += line + "\n"

        else:

            text += (
                f"{WEEKDAYS[i]} — нет\n"
            )

    text += "\n"

    # ==================================================
    # САХАР
    # ==================================================

    text += "🩸 <b>Сахар</b>\n"

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()
        items = blood_sugar.get(key, [])

        text += f"\n<b>{WEEKDAYS[i]}</b>\n"

        if not items:
            text += "нет\n"
            continue

        for m in items:
            time_text = m["time"] or "--:--"
            text += (
                f"{time_text} — "
                f"<b>{m['value']}</b> "
                f"({m['meal_label']})\n"
            )

    text += "\n"

    # ==================================================
    # МИГРЕНЬ
    # ==================================================

    text += "🧠 <b>Мигрень</b>\n"

    migraine_count = 0

    for i in range(7):

        current = monday + timedelta(
            days=i
        )

        key = current.isoformat()

        info = migraine.get(
            key
        )

        if info:

            migraine_count += 1

            text += (
                f"{WEEKDAYS[i]} — "
                f"{info['intensity']}/10"
                f" ({info['time'] or '--:--'})\n"
            )

        else:

            text += (
                f"{WEEKDAYS[i]} — нет\n"
            )

    text += (
        f"\nВсего эпизодов: "
        f"<b>{migraine_count}</b>\n"
    )

    return text


# ==================================================
# МЕСЯЧНЫЙ ОТЧЁТ
# ==================================================

def build_month_report(
    user_id,
    target_date
):

    first_day = target_date.replace(
        day=1
    )

    last_day = target_date.replace(
        day=calendar.monthrange(
            target_date.year,
            target_date.month
        )[1]
    )

    water = get_water(
        user_id,
        first_day,
        last_day
    )

    toilet = get_toilet(
        user_id,
        first_day,
        last_day
    )

    blood_pressure = get_blood_pressure(
        user_id,
        first_day,
        last_day
    )

    sleep = get_sleep(
        user_id,
        first_day,
        last_day
    )

    work = get_work(
        user_id,
        first_day,
        last_day
    )

    blood_sugar = get_blood_sugar(
        user_id,
        first_day,
        last_day
    )

    text = (
        f"📊 <b>{MONTHS[target_date.month - 1]} "
        f"{target_date.year}</b>\n\n"
    )

    # ==================================================
    # ВОДА
    # ==================================================

    text += "💧 <b>Вода</b>\n"

    month_water = 0

    current = first_day

    while current <= last_day:

        key = current.isoformat()

        count = water.get(
            key,
            0
        )

        month_water += count

        text += (
            f"{current.day:02d} — "
            f"{count} × 200 мл\n"
        )

        current += timedelta(
            days=1
        )

    text += (
        f"\nИтого: "
        f"<b>{month_water * 200} мл</b>\n\n"
    )

    # ==================================================
    # СТУЛ
    # ==================================================

    text += "🚻 <b>Стул</b>\n"

    current = first_day

    while current <= last_day:

        key = current.isoformat()

        visits = toilet.get(
            key,
            []
        )

        if visits:

            text += (
                f"\n<b>{current.day:02d} "
                f"{MONTHS[current.month - 1]}</b>\n"
            )

            for visit in visits:

                time_text = (
                    visit["time"]
                    or "--:--"
                )

                stool_type = (
                    STOOL_TYPES.get(
                        visit["type"],
                        visit["type"]
                    )
                    if visit["type"]
                    else "тип не указан"
                )

                text += (
                    f"{time_text} — "
                    f"{stool_type}\n"
                )

        current += timedelta(
            days=1
        )

    text += "\n"

    # ==================================================
    # ДАВЛЕНИЕ
    # ==================================================

    text += "🩺 <b>Давление</b>\n"

    pressure_count = 0

    current = first_day

    while current <= last_day:

        key = current.isoformat()

        measurements = blood_pressure.get(
            key,
            []
        )

        if measurements:

            text += (
                f"\n<b>{current.strftime('%d.%m')}</b>\n"
            )

            for measurement in measurements:

                text += (
                    format_pressure(
                        measurement
                    )
                    + "\n"
                )

                pressure_count += 1

        current += timedelta(
            days=1
        )

    if pressure_count == 0:

        text += (
            "Нет измерений\n"
        )

    else:

        text += (
            f"\nВсего измерений: "
            f"<b>{pressure_count}</b>\n"
        )

    # ==================================================
    # СОН
    # ==================================================

    text += "😴 <b>Сон</b>\n"

    current = first_day

    while current <= last_day:

        key = current.isoformat()
        info = sleep.get(key)

        if info:
            started = info["started"] or "--:--"
            wake_up = info["wake_up"] or "--:--"
            duration = info.get("duration")
            line = f"{current.day:02d} — {started} — {wake_up}"
            if duration:
                line += f" ({duration})"
            text += line + "\n"
        else:
            text += f"{current.day:02d} — нет\n"

        current += timedelta(days=1)

    text += "\n"

    # ==================================================
    # РАБОТА
    # ==================================================

    text += "💼 <b>Работа</b>\n"

    current = first_day

    while current <= last_day:

        key = current.isoformat()
        info = work.get(key)

        if info:
            started = info["started"] or "--:--"
            finished = info["finished"] or "--:--"
            duration = info.get("duration")
            line = f"{current.day:02d} — {started} — {finished}"
            if duration:
                line += f" ({duration})"
            text += line + "\n"
        else:
            text += f"{current.day:02d} — нет\n"

        current += timedelta(days=1)

    text += "\n"

    return text


# ==================================================
# ГОДОВОЙ ОТЧЁТ
# ==================================================

def build_year_report(
    user_id,
    target_date
):

    first_day = date(
        target_date.year,
        1,
        1
    )

    last_day = date(
        target_date.year,
        12,
        31
    )

    water = get_water(
        user_id,
        first_day,
        last_day
    )

    toilet = get_toilet(
        user_id,
        first_day,
        last_day
    )

    blood_pressure = get_blood_pressure(
        user_id,
        first_day,
        last_day
    )

    sleep = get_sleep(
        user_id,
        first_day,
        last_day
    )

    work = get_work(
        user_id,
        first_day,
        last_day
    )

    blood_sugar = get_blood_sugar(
        user_id,
        first_day,
        last_day
    )

    text = (
        f"📊 <b>{target_date.year} год</b>\n\n"
    )

    # ==================================================
    # ВОДА
    # ==================================================

    text += "💧 <b>Вода</b>\n"

    year_water = 0

    for month in range(1, 13):

        days_in_month = calendar.monthrange(
            target_date.year,
            month
        )[1]

        month_count = 0

        for day_number in range(
            1,
            days_in_month + 1
        ):

            current = date(
                target_date.year,
                month,
                day_number
            )

            month_count += water.get(
                current.isoformat(),
                0
            )

        year_water += month_count

        text += (
            f"{MONTHS[month - 1]} — "
            f"{month_count} × 200 мл\n"
        )

    text += (
        f"\nИтого за год: "
        f"<b>{year_water * 200} мл</b>\n\n"
    )

    # ==================================================
    # СТУЛ
    # ==================================================

    text += "🚻 <b>Стул</b>\n"

    for month in range(1, 13):

        month_count = 0

        days_in_month = calendar.monthrange(
            target_date.year,
            month
        )[1]

        for day_number in range(
            1,
            days_in_month + 1
        ):

            current = date(
                target_date.year,
                month,
                day_number
            )

            month_count += len(
                toilet.get(
                    current.isoformat(),
                    []
                )
            )

        text += (
            f"{MONTHS[month - 1]} — "
            f"{month_count} раз\n"
        )

    text += "\n"

    # ==================================================
    # ДАВЛЕНИЕ
    # ==================================================

    text += "🩺 <b>Давление</b>\n"

    for month in range(1, 13):

        days_in_month = calendar.monthrange(
            target_date.year,
            month
        )[1]

        month_measurements = []

        for day_number in range(
            1,
            days_in_month + 1
        ):

            current = date(
                target_date.year,
                month,
                day_number
            )

            measurements = blood_pressure.get(
                current.isoformat(),
                []
            )

            month_measurements.extend(
                measurements
            )

        if not month_measurements:

            text += (
                f"{MONTHS[month - 1]} — "
                f"нет измерений\n"
            )

            continue

        systolic_values = [
            m["systolic"]
            for m in month_measurements
            if m["systolic"] is not None
        ]

        diastolic_values = [
            m["diastolic"]
            for m in month_measurements
            if m["diastolic"] is not None
        ]

        pulse_values = [
            m["pulse"]
            for m in month_measurements
            if m["pulse"] is not None
        ]

        average_systolic = (
            round(
                sum(systolic_values)
                / len(systolic_values)
            )
            if systolic_values
            else None
        )

        average_diastolic = (
            round(
                sum(diastolic_values)
                / len(diastolic_values)
            )
            if diastolic_values
            else None
        )

        average_pulse = (
            round(
                sum(pulse_values)
                / len(pulse_values)
            )
            if pulse_values
            else None
        )

        text += (
            f"{MONTHS[month - 1]} — "
            f"<b>{len(month_measurements)}</b> измерений"
        )

        if (
            average_systolic is not None
            and average_diastolic is not None
        ):

            text += (
                f", среднее "
                f"<b>{average_systolic}/"
                f"{average_diastolic}</b>"
            )

        if average_pulse is not None:

            text += (
                f", пульс "
                f"<b>{average_pulse}</b>"
            )

        text += "\n"

    # ==================================================
    # САХАР
    # ==================================================

    text += "🩸 <b>Сахар</b>\n"

    year_sugar_count = 0

    for month in range(1, 13):

        days_in_month = calendar.monthrange(
            target_date.year,
            month
        )[1]

        month_measurements = []

        for day_number in range(1, days_in_month + 1):
            current = date(
                target_date.year,
                month,
                day_number
            )
            month_measurements.extend(
                blood_sugar.get(current.isoformat(), [])
            )

        year_sugar_count += len(month_measurements)

        if not month_measurements:
            text += f"{MONTHS[month - 1]} — нет измерений\n"
            continue

        text += (
            f"{MONTHS[month - 1]} — "
            f"<b>{len(month_measurements)}</b> измерений\n"
        )

    text += (
        f"\nВсего измерений за год: "
        f"<b>{year_sugar_count}</b>\n\n"
    )

    # ==================================================
    # СОН
    # ==================================================

    text += "😴 <b>Сон</b>\n"

    for month in range(1, 13):

        days_in_month = calendar.monthrange(
            target_date.year,
            month
        )[1]

        days_with_sleep = 0
        total_minutes = 0

        for day_number in range(1, days_in_month + 1):

            current = date(
                target_date.year,
                month,
                day_number
            )
            info = sleep.get(current.isoformat())

            if info and info.get("started"):
                days_with_sleep += 1
                if info.get("duration"):
                    # parse "X ч Y мин"
                    try:
                        parts = info["duration"].replace("ч", " ").replace("мин", " ").split()
                        h = int(parts[0]) if parts else 0
                        m = int(parts[1]) if len(parts) > 1 else 0
                        total_minutes += h * 60 + m
                    except Exception:
                        pass

        if days_with_sleep == 0:
            text += f"{MONTHS[month - 1]} — нет записей\n"
        else:
            avg = ""
            if total_minutes and days_with_sleep:
                avg_m = total_minutes // days_with_sleep
                avg = f", среднее {avg_m // 60} ч {avg_m % 60} мин"
            text += (
                f"{MONTHS[month - 1]} — "
                f"<b>{days_with_sleep}</b> ночей{avg}\n"
            )

    text += "\n"

    # ==================================================
    # РАБОТА
    # ==================================================

    text += "💼 <b>Работа</b>\n"

    for month in range(1, 13):

        days_in_month = calendar.monthrange(
            target_date.year,
            month
        )[1]

        days_with_work = 0
        total_minutes = 0

        for day_number in range(1, days_in_month + 1):

            current = date(
                target_date.year,
                month,
                day_number
            )
            info = work.get(current.isoformat())

            if info and info.get("started"):
                days_with_work += 1
                if info.get("duration"):
                    try:
                        parts = info["duration"].replace("ч", " ").replace("мин", " ").split()
                        h = int(parts[0]) if parts else 0
                        m = int(parts[1]) if len(parts) > 1 else 0
                        total_minutes += h * 60 + m
                    except Exception:
                        pass

        if days_with_work == 0:
            text += f"{MONTHS[month - 1]} — нет записей\n"
        else:
            avg = ""
            if total_minutes and days_with_work:
                avg_m = total_minutes // days_with_work
                avg = f", среднее {avg_m // 60} ч {avg_m % 60} мин"
            text += (
                f"{MONTHS[month - 1]} — "
                f"<b>{days_with_work}</b> дней{avg}\n"
            )

    text += "\n"

    return text