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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ОТЧЁТОВ
# ==================================================

def iter_dates(start_date, end_date):
    """Перебирает даты включительно."""
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def recorded_dates(data):
    """Возвращает отсортированные даты, по которым есть данные."""
    return sorted(
        date.fromisoformat(key)
        for key, value in data.items()
        if value
    )


def duration_to_minutes(value):
    """Преобразует строку вида '8 ч 25 мин' в минуты."""
    if not value:
        return None
    try:
        parts = value.replace("ч", " ").replace("мин", " ").split()
        hours = int(parts[0]) if parts else 0
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return hours * 60 + minutes
    except (ValueError, TypeError, IndexError):
        return None


def format_minutes(total_minutes):
    if total_minutes is None:
        return None
    return f"{total_minutes // 60} ч {total_minutes % 60} мин"


def section(title, lines):
    """Добавляет раздел, только если в нём есть данные."""
    lines = [line for line in lines if line]
    if not lines:
        return ""
    return title + "\n" + "\n".join(lines)


def date_label(day):
    return f"{WEEKDAYS[day.weekday()]} {day.strftime('%d.%m')}"


def collect_measurements_by_month(data, year, month):
    result = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        key = date(year, month, day).isoformat()
        result.extend(data.get(key, []))
    return result


# ==================================================
# ДНЕВНОЙ ОТЧЁТ
# ==================================================

def build_day_report(user_id, target_date):
    start_date = target_date
    end_date = target_date

    water = get_water(user_id, start_date, end_date)
    toilet = get_toilet(user_id, start_date, end_date)
    sleep = get_sleep(user_id, start_date, end_date)
    work = get_work(user_id, start_date, end_date)
    migraine = get_migraine(user_id, start_date, end_date)
    habits = get_habits(user_id, start_date, end_date)
    blood_pressure = get_blood_pressure(user_id, start_date, end_date)
    blood_sugar = get_blood_sugar(user_id, start_date, end_date)

    key = target_date.isoformat()
    sections = []

    water_count = water.get(key, 0)
    if water_count > 0:
        sections.append(section(
            "💧 <b>Вода</b>",
            [f"{water_count} × 200 мл = <b>{water_count * 200} мл</b>"]
        ))

    visits = toilet.get(key, [])
    if visits:
        lines = [f"Всего: <b>{len(visits)}</b> раз"]
        for visit in visits:
            time_text = visit["time"] or "--:--"
            stool_type = STOOL_TYPES.get(visit["type"], visit["type"]) if visit["type"] else "тип не указан"
            lines.append(f"{time_text} — {stool_type}")
        sections.append(section("🚻 <b>Стул</b>", lines))

    pressure_measurements = blood_pressure.get(key, [])
    if pressure_measurements:
        sections.append(section(
            "🩺 <b>Давление</b>",
            [format_pressure(item) for item in pressure_measurements]
        ))

    sugar_measurements = blood_sugar.get(key, [])
    if sugar_measurements:
        lines = []
        for item in sugar_measurements:
            lines.append(
                f"{item['time'] or '--:--'} — <b>{item['value']}</b> ммоль/л "
                f"({item['meal_label']})"
            )
        sections.append(section("🩸 <b>Сахар</b>", lines))

    migraine_info = migraine.get(key)
    if migraine_info:
        sections.append(section(
            "🧠 <b>Мигрень</b>",
            [f"{migraine_info['time'] or '--:--'} — {migraine_info['intensity']}/10"]
        ))

    sleep_info = sleep.get(key)
    if sleep_info and (sleep_info.get("started") or sleep_info.get("wake_up")):
        started = sleep_info.get("started") or "--:--"
        wake_up = sleep_info.get("wake_up") or "--:--"
        duration = sleep_info.get("duration")
        line = f"{started} — {wake_up}"
        if duration:
            line += f" ({duration})"
        sections.append(section("😴 <b>Сон</b>", [line]))

    work_info = work.get(key)
    if work_info and (work_info.get("started") or work_info.get("finished")):
        started = work_info.get("started") or "--:--"
        finished = work_info.get("finished") or "--:--"
        duration = work_info.get("duration")
        line = f"{started} — {finished}"
        if duration:
            line += f" ({duration})"
        sections.append(section("💼 <b>Работа</b>", [line]))

    habit_list = habits.get(key, [])
    if habit_list:
        lines = []
        for habit in habit_list:
            time_text = f" — {habit['time']}" if habit.get("time") else ""
            lines.append(f"☑ {habit['title']}{time_text}")
        sections.append(section("⭐ <b>Привычки</b>", lines))

    header = (
        f"📅 <b>{WEEKDAYS[target_date.weekday()]}, "
        f"{target_date.strftime('%d.%m.%Y')}</b>"
    )
    body = "\n\n".join(item for item in sections if item)
    if not body:
        body = "За этот день пока нет записей."
    return header + "\n\n" + body


# ==================================================
# НЕДЕЛЬНЫЙ ОТЧЁТ
# ==================================================

def build_week_report(user_id, target_date):
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)

    water = get_water(user_id, monday, sunday)
    toilet = get_toilet(user_id, monday, sunday)
    migraine = get_migraine(user_id, monday, sunday)
    blood_pressure = get_blood_pressure(user_id, monday, sunday)
    sleep = get_sleep(user_id, monday, sunday)
    work = get_work(user_id, monday, sunday)
    blood_sugar = get_blood_sugar(user_id, monday, sunday)

    sections = []
    water_dates = recorded_dates({k: v for k, v in water.items() if v > 0})
    if water_dates:
        lines = []
        total_water = 0
        for day in water_dates:
            count = water[day.isoformat()]
            total_water += count
            lines.append(f"{date_label(day)} — {count} × 200 мл")
        lines.append(f"Итого: <b>{total_water * 200} мл</b>")
        sections.append(section("💧 <b>Вода</b>", lines))

    toilet_dates = recorded_dates(toilet)
    if toilet_dates:
        lines = []
        total = 0
        for day in toilet_dates:
            visits = toilet[day.isoformat()]
            total += len(visits)
            lines.append(f"<b>{date_label(day)}</b>")
            for visit in visits:
                stool_type = STOOL_TYPES.get(visit["type"], visit["type"]) if visit["type"] else "тип не указан"
                lines.append(f"{visit['time'] or '--:--'} — {stool_type}")
        lines.append(f"Всего: <b>{total}</b> посещений")
        sections.append(section("🚻 <b>Стул</b>", lines))

    pressure_dates = recorded_dates(blood_pressure)
    if pressure_dates:
        lines = []
        count = 0
        for day in pressure_dates:
            measurements = blood_pressure[day.isoformat()]
            lines.append(f"<b>{date_label(day)}</b>")
            for item in measurements:
                lines.append(format_pressure(item))
                count += 1
        lines.append(f"Всего измерений: <b>{count}</b>")
        sections.append(section("🩺 <b>Давление</b>", lines))

    sugar_dates = recorded_dates(blood_sugar)
    if sugar_dates:
        lines = []
        count = 0
        for day in sugar_dates:
            measurements = blood_sugar[day.isoformat()]
            lines.append(f"<b>{date_label(day)}</b>")
            for item in measurements:
                lines.append(
                    f"{item['time'] or '--:--'} — <b>{item['value']}</b> ммоль/л "
                    f"({item['meal_label']})"
                )
                count += 1
        lines.append(f"Всего измерений: <b>{count}</b>")
        sections.append(section("🩸 <b>Сахар</b>", lines))

    sleep_dates = [day for day in recorded_dates(sleep)
                   if sleep[day.isoformat()].get("started") or sleep[day.isoformat()].get("wake_up")]
    if sleep_dates:
        lines = []
        for day in sleep_dates:
            info = sleep[day.isoformat()]
            started = info.get("started") or "--:--"
            wake_up = info.get("wake_up") or "--:--"
            line = f"{date_label(day)} — {started} — {wake_up}"
            if info.get("duration"):
                line += f" ({info['duration']})"
            lines.append(line)
        sections.append(section("😴 <b>Сон</b>", lines))

    work_dates = [day for day in recorded_dates(work)
                  if work[day.isoformat()].get("started") or work[day.isoformat()].get("finished")]
    if work_dates:
        lines = []
        for day in work_dates:
            info = work[day.isoformat()]
            started = info.get("started") or "--:--"
            finished = info.get("finished") or "--:--"
            line = f"{date_label(day)} — {started} — {finished}"
            if info.get("duration"):
                line += f" ({info['duration']})"
            lines.append(line)
        sections.append(section("💼 <b>Работа</b>", lines))

    migraine_dates = recorded_dates(migraine)
    if migraine_dates:
        lines = []
        for day in migraine_dates:
            info = migraine[day.isoformat()]
            lines.append(f"{date_label(day)} — {info['intensity']}/10 ({info['time'] or '--:--'})")
        lines.append(f"Всего эпизодов: <b>{len(migraine_dates)}</b>")
        sections.append(section("🧠 <b>Мигрень</b>", lines))

    header = (
        f"📊 <b>Неделя</b>\n"
        f"{monday.strftime('%d.%m')} — {sunday.strftime('%d.%m.%Y')}"
    )
    body = "\n\n".join(item for item in sections if item)
    if not body:
        body = "За эту неделю пока нет записей."
    return header + "\n\n" + body


# ==================================================
# МЕСЯЧНЫЙ ОТЧЁТ
# ==================================================

def build_month_report(user_id, target_date):
    first_day = target_date.replace(day=1)
    last_day = target_date.replace(day=calendar.monthrange(target_date.year, target_date.month)[1])

    water = get_water(user_id, first_day, last_day)
    toilet = get_toilet(user_id, first_day, last_day)
    blood_pressure = get_blood_pressure(user_id, first_day, last_day)
    sleep = get_sleep(user_id, first_day, last_day)
    work = get_work(user_id, first_day, last_day)
    blood_sugar = get_blood_sugar(user_id, first_day, last_day)

    sections = []

    water_dates = recorded_dates({k: v for k, v in water.items() if v > 0})
    if water_dates:
        lines = []
        total_water = 0
        for day in water_dates:
            count = water[day.isoformat()]
            total_water += count
            lines.append(f"{day.strftime('%d.%m')} — {count} × 200 мл")
        lines.append(f"Итого: <b>{total_water * 200} мл</b>")
        sections.append(section("💧 <b>Вода</b>", lines))

    toilet_dates = recorded_dates(toilet)
    if toilet_dates:
        lines = []
        total_visits = 0
        for day in toilet_dates:
            visits = toilet[day.isoformat()]
            total_visits += len(visits)
            lines.append(f"<b>{day.strftime('%d.%m')}</b>")
            for visit in visits:
                stool_type = STOOL_TYPES.get(visit["type"], visit["type"]) if visit["type"] else "тип не указан"
                lines.append(f"{visit['time'] or '--:--'} — {stool_type}")
        lines.append(f"Всего посещений: <b>{total_visits}</b>")
        sections.append(section("🚻 <b>Стул</b>", lines))

    pressure_dates = recorded_dates(blood_pressure)
    if pressure_dates:
        lines = []
        count = 0
        for day in pressure_dates:
            measurements = blood_pressure[day.isoformat()]
            lines.append(f"<b>{day.strftime('%d.%m')}</b>")
            for item in measurements:
                lines.append(format_pressure(item))
                count += 1
        lines.append(f"Всего измерений: <b>{count}</b>")
        sections.append(section("🩺 <b>Давление</b>", lines))

    sugar_dates = recorded_dates(blood_sugar)
    if sugar_dates:
        lines = []
        count = 0
        for day in sugar_dates:
            measurements = blood_sugar[day.isoformat()]
            lines.append(f"<b>{day.strftime('%d.%m')}</b>")
            for item in measurements:
                lines.append(
                    f"{item['time'] or '--:--'} — <b>{item['value']}</b> ммоль/л "
                    f"({item['meal_label']})"
                )
                count += 1
        lines.append(f"Всего измерений: <b>{count}</b>")
        sections.append(section("🩸 <b>Сахар</b>", lines))

    sleep_dates = [day for day in recorded_dates(sleep)
                   if sleep[day.isoformat()].get("started") or sleep[day.isoformat()].get("wake_up")]
    if sleep_dates:
        lines = []
        for day in sleep_dates:
            info = sleep[day.isoformat()]
            line = f"{day.strftime('%d')} — {info.get('started') or '--:--'} — {info.get('wake_up') or '--:--'}"
            if info.get("duration"):
                line += f" ({info['duration']})"
            lines.append(line)
        sections.append(section("😴 <b>Сон</b>", lines))

    work_dates = [day for day in recorded_dates(work)
                  if work[day.isoformat()].get("started") or work[day.isoformat()].get("finished")]
    if work_dates:
        lines = []
        for day in work_dates:
            info = work[day.isoformat()]
            line = f"{day.strftime('%d')} — {info.get('started') or '--:--'} — {info.get('finished') or '--:--'}"
            if info.get("duration"):
                line += f" ({info['duration']})"
            lines.append(line)
        sections.append(section("💼 <b>Работа</b>", lines))

    header = f"📊 <b>{MONTHS[target_date.month - 1]} {target_date.year}</b>"
    body = "\n\n".join(item for item in sections if item)
    if not body:
        body = "За этот месяц пока нет записей."
    return header + "\n\n" + body


# ==================================================
# ГОДОВОЙ ОТЧЁТ
# ==================================================

def build_year_report(user_id, target_date):
    first_day = date(target_date.year, 1, 1)
    last_day = date(target_date.year, 12, 31)

    water = get_water(user_id, first_day, last_day)
    toilet = get_toilet(user_id, first_day, last_day)
    blood_pressure = get_blood_pressure(user_id, first_day, last_day)
    sleep = get_sleep(user_id, first_day, last_day)
    work = get_work(user_id, first_day, last_day)
    blood_sugar = get_blood_sugar(user_id, first_day, last_day)

    sections = []

    # Вода — показываем только месяцы с записями.
    month_water_counts = {}
    for day in recorded_dates({k: v for k, v in water.items() if v > 0}):
        month_water_counts[day.month] = month_water_counts.get(day.month, 0) + water[day.isoformat()]
    if month_water_counts:
        lines = [f"{MONTHS[m - 1]} — {count * 200} мл" for m, count in sorted(month_water_counts.items())]
        lines.append(f"Итого за год: <b>{sum(month_water_counts.values()) * 200} мл</b>")
        sections.append(section("💧 <b>Вода</b>", lines))

    # Стул — только месяцы с зарегистрированными посещениями.
    toilet_month_counts = {}
    for day in recorded_dates(toilet):
        toilet_month_counts[day.month] = toilet_month_counts.get(day.month, 0) + len(toilet[day.isoformat()])
    if toilet_month_counts:
        lines = [f"{MONTHS[m - 1]} — {count} посещений" for m, count in sorted(toilet_month_counts.items())]
        lines.append(f"Всего за год: <b>{sum(toilet_month_counts.values())}</b>")
        sections.append(section("🚻 <b>Стул</b>", lines))

    # Давление — только месяцы, в которых есть измерения.
    pressure_months = {}
    for day in recorded_dates(blood_pressure):
        pressure_months.setdefault(day.month, []).extend(blood_pressure[day.isoformat()])
    if pressure_months:
        lines = []
        total = 0
        for month, measurements in sorted(pressure_months.items()):
            total += len(measurements)
            systolic = [m["systolic"] for m in measurements if m.get("systolic") is not None]
            diastolic = [m["diastolic"] for m in measurements if m.get("diastolic") is not None]
            pulse = [m["pulse"] for m in measurements if m.get("pulse") is not None]
            line = f"{MONTHS[month - 1]} — <b>{len(measurements)}</b> измерений"
            if systolic and diastolic:
                line += f", среднее <b>{round(sum(systolic) / len(systolic))}/{round(sum(diastolic) / len(diastolic))}</b>"
            if pulse:
                line += f", пульс <b>{round(sum(pulse) / len(pulse))}</b>"
            lines.append(line)
        lines.append(f"Всего измерений за год: <b>{total}</b>")
        sections.append(section("🩺 <b>Давление</b>", lines))

    # Сахар — только месяцы, в которых есть измерения.
    sugar_months = {}
    for day in recorded_dates(blood_sugar):
        sugar_months.setdefault(day.month, []).extend(blood_sugar[day.isoformat()])
    if sugar_months:
        lines = []
        total = 0
        for month, measurements in sorted(sugar_months.items()):
            total += len(measurements)
            lines.append(f"{MONTHS[month - 1]} — <b>{len(measurements)}</b> измерений")
        lines.append(f"Всего измерений за год: <b>{total}</b>")
        sections.append(section("🩸 <b>Сахар</b>", lines))

    # Сон — только месяцы с начатыми снами.
    sleep_month_counts = {}
    sleep_minutes = {}
    for day in recorded_dates(sleep):
        info = sleep[day.isoformat()]
        if not (info.get("started") or info.get("wake_up")):
            continue
        sleep_month_counts[day.month] = sleep_month_counts.get(day.month, 0) + 1
        minutes = duration_to_minutes(info.get("duration"))
        if minutes is not None:
            sleep_minutes[day.month] = sleep_minutes.get(day.month, 0) + minutes
    if sleep_month_counts:
        lines = []
        for month, count in sorted(sleep_month_counts.items()):
            line = f"{MONTHS[month - 1]} — <b>{count}</b> ночей"
            if sleep_minutes.get(month):
                avg = sleep_minutes[month] // count
                line += f", среднее {format_minutes(avg)}"
            lines.append(line)
        sections.append(section("😴 <b>Сон</b>", lines))

    # Работа — только месяцы с записями.
    work_month_counts = {}
    work_minutes = {}
    for day in recorded_dates(work):
        info = work[day.isoformat()]
        if not (info.get("started") or info.get("finished")):
            continue
        work_month_counts[day.month] = work_month_counts.get(day.month, 0) + 1
        minutes = duration_to_minutes(info.get("duration"))
        if minutes is not None:
            work_minutes[day.month] = work_minutes.get(day.month, 0) + minutes
    if work_month_counts:
        lines = []
        for month, count in sorted(work_month_counts.items()):
            line = f"{MONTHS[month - 1]} — <b>{count}</b> рабочих дней"
            if work_minutes.get(month):
                avg = work_minutes[month] // count
                line += f", среднее {format_minutes(avg)}"
            lines.append(line)
        sections.append(section("💼 <b>Работа</b>", lines))

    header = f"📊 <b>{target_date.year} год</b>"
    body = "\n\n".join(item for item in sections if item)
    if not body:
        body = "За этот год пока нет записей."
    return header + "\n\n" + body
