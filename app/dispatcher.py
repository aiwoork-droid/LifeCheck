from app.handlers import menu_handler
from app.handlers import day_handler
from app.handlers import habits_handler
from app.handlers import today_handler

from database.repositories.users import users
from database.repositories.blood_pressure_logs import blood_pressure_logs


class Dispatcher:

    def dispatch(
        self,
        api,
        message,
        screen
    ):

        text = message["body"].get(
            "text",
            ""
        ).strip()

        sender = message["sender"]

        first_name = sender.get(
            "first_name",
            ""
        )

        chat_id = message[
            "recipient"
        ]["chat_id"]

        user_id = sender[
            "user_id"
        ]

        # ==========================================
        # Главное меню
        # ==========================================

        if screen == "menu":

            menu_handler.handle(
                api,
                chat_id,
                user_id,
                first_name,
                text
            )

            return

        # ==========================================
        # Здоровье
        # ==========================================

        elif screen == "health":

            if text == "0":

                users.set_screen(
                    user_id,
                    "menu"
                )

                from app.commands import menu

                menu.execute(
                    api,
                    chat_id,
                    first_name
                )

                return

            if text == "1":

                users.set_screen(
                    user_id,
                    "health_pressure"
                )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "🩺 <b>Давление</b>\n\n"
                        "1 — Новое измерение\n"
                        "2 — Сегодня\n"
                        "3 — Удалить последнее\n\n"
                        "0 — назад"
                    )
                )

                return

            if text == "2":

                users.set_screen(
                    user_id,
                    "migraine_intensity"
                )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "🧠 <b>Мигрень</b>\n\n"
                        "Укажите силу боли "
                        "от 1 до 10.\n\n"
                        "1 — очень слабо\n"
                        "10 — очень сильно\n\n"
                        "0 — отмена"
                    )
                )

                return

            api.send_message(
                chat_id=chat_id,
                text=(
                    "❤️ <b>Здоровье</b>\n\n"
                    "1 — 🩺 Давление\n"
                    "2 — 🧠 Мигрень\n\n"
                    "0 — назад"
                )
            )

            return

        # ==========================================
        # Раздел давления
        # ==========================================

        elif screen == "health_pressure":

            if text == "0":

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

                return

            if text == "1":

                users.set_screen(
                    user_id,
                    "blood_pressure_systolic"
                )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "🩺 <b>Новое измерение</b>\n\n"
                        "Введите верхнее давление.\n\n"
                        "Например: <b>120</b>\n\n"
                        "0 — отмена"
                    )
                )

                return

            if text == "2":

                measurements = (
                    blood_pressure_logs
                    .get_today_measurements(
                        user_id
                    )
                )

                if not measurements:

                    result = (
                        "🩺 <b>Давление сегодня</b>\n\n"
                        "Измерений пока нет."
                    )

                else:

                    result = (
                        "🩺 <b>Давление сегодня</b>\n\n"
                    )

                    for measurement in measurements:

                        time_text = (
                            measurement["time"]
                            or "--:--"
                        )

                        result += (
                            f"{time_text} — "
                            f"{measurement['systolic']}/"
                            f"{measurement['diastolic']}, "
                            f"пульс "
                            f"{measurement['pulse']}\n"
                        )

                result += "\n0 — назад"

                api.send_message(
                    chat_id=chat_id,
                    text=result
                )

                return

            if text == "3":

                removed = (
                    blood_pressure_logs
                    .remove_last_measurement(
                        user_id
                    )
                )

                if removed:

                    text_result = (
                        "🩺 Последнее измерение "
                        "удалено."
                    )

                else:

                    text_result = (
                        "🩺 Сегодня нет измерений."
                    )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        text_result
                        + "\n\n"
                        + "0 — назад"
                    )
                )

                return

            api.send_message(
                chat_id=chat_id,
                text=(
                    "🩺 <b>Давление</b>\n\n"
                    "1 — Новое измерение\n"
                    "2 — Сегодня\n"
                    "3 — Удалить последнее\n\n"
                    "0 — назад"
                )
            )

            return

        # ==========================================
        # Ввод верхнего давления
        # ==========================================

        elif screen == "blood_pressure_systolic":

            if text == "0":

                users.set_screen(
                    user_id,
                    "health_pressure"
                )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "🩺 <b>Давление</b>\n\n"
                        "1 — Новое измерение\n"
                        "2 — Сегодня\n"
                        "3 — Удалить последнее\n\n"
                        "0 — назад"
                    )
                )

                return

            if not text.isdigit():

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Введите число.\n"
                        "Например: <b>120</b>"
                    )
                )

                return

            systolic = int(text)

            if systolic < 50 or systolic > 250:

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Значение выглядит "
                        "необычно.\n\n"
                        "Введите верхнее давление "
                        "от 50 до 250."
                    )
                )

                return

            users.set_screen(
                user_id,
                "blood_pressure_diastolic"
            )

            users.set_temp_value(
                user_id,
                "blood_pressure_systolic",
                systolic
            )

            api.send_message(
                chat_id=chat_id,
                text=(
                    "🩺 Верхнее давление: "
                    f"<b>{systolic}</b>\n\n"
                    "Теперь введите нижнее "
                    "давление.\n\n"
                    "Например: <b>80</b>\n\n"
                    "0 — отмена"
                )
            )

            return

        # ==========================================
        # Ввод нижнего давления
        # ==========================================

        elif screen == "blood_pressure_diastolic":

            if text == "0":

                users.set_screen(
                    user_id,
                    "health_pressure"
                )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "🩺 <b>Давление</b>\n\n"
                        "1 — Новое измерение\n"
                        "2 — Сегодня\n"
                        "3 — Удалить последнее\n\n"
                        "0 — назад"
                    )
                )

                return

            if not text.isdigit():

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Введите число.\n"
                        "Например: <b>80</b>"
                    )
                )

                return

            diastolic = int(text)

            if diastolic < 30 or diastolic > 150:

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Значение выглядит "
                        "необычно.\n\n"
                        "Введите нижнее давление "
                        "от 30 до 150."
                    )
                )

                return

            systolic = users.get_temp_value(
                user_id,
                "blood_pressure_systolic"
            )

            if systolic is None:

                users.set_screen(
                    user_id,
                    "health_pressure"
                )

                api.send_message(
                    chat_id=chat_id,
                    text="Начните измерение заново."
                )

                return

            users.set_temp_value(
                user_id,
                "blood_pressure_diastolic",
                diastolic
            )

            users.set_screen(
                user_id,
                "blood_pressure_pulse"
            )

            api.send_message(
                chat_id=chat_id,
                text=(
                    "🩺 Давление: "
                    f"<b>{systolic}/{diastolic}</b>\n\n"
                    "Теперь введите пульс.\n\n"
                    "Например: <b>72</b>\n\n"
                    "0 — отмена"
                )
            )

            return

        # ==========================================
        # Ввод пульса
        # ==========================================

        elif screen == "blood_pressure_pulse":

            if text == "0":

                users.set_screen(
                    user_id,
                    "health_pressure"
                )

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "🩺 <b>Давление</b>\n\n"
                        "1 — Новое измерение\n"
                        "2 — Сегодня\n"
                        "3 — Удалить последнее\n\n"
                        "0 — назад"
                    )
                )

                return

            if not text.isdigit():

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Введите число.\n"
                        "Например: <b>72</b>"
                    )
                )

                return

            pulse = int(text)

            if pulse < 30 or pulse > 220:

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Значение выглядит "
                        "необычно.\n\n"
                        "Введите пульс "
                        "от 30 до 220."
                    )
                )

                return

            systolic = users.get_temp_value(
                user_id,
                "blood_pressure_systolic"
            )

            diastolic = users.get_temp_value(
                user_id,
                "blood_pressure_diastolic"
            )

            if systolic is None or diastolic is None:

                users.set_screen(
                    user_id,
                    "health_pressure"
                )

                api.send_message(
                    chat_id=chat_id,
                    text="Начните измерение заново."
                )

                return

            blood_pressure_logs.add_measurement(
                user_id,
                systolic,
                diastolic,
                pulse
            )

            users.set_screen(
                user_id,
                "health_pressure"
            )

            api.send_message(
                chat_id=chat_id,
                text=(
                    "✅ <b>Измерение сохранено</b>\n\n"
                    f"🩺 {systolic}/{diastolic}\n"
                    f"❤️ Пульс: {pulse}\n\n"
                    "Время записано автоматически.\n\n"
                    "1 — Новое измерение\n"
                    "2 — Сегодня\n"
                    "3 — Удалить последнее\n\n"
                    "0 — назад"
                )
            )

            return

        # ==========================================
        # Сегодня + состояния раздела «Сегодня»
        # ==========================================

        elif screen in (
            "today",
            "toilet_type",
            "toilet_amount",
            "toilet_time"
        ):

            today_handler.handle(
                api,
                chat_id,
                user_id,
                first_name,
                text
            )

            return

        # ==========================================
        # Мигрень
        # ==========================================

        elif screen == "migraine_intensity":

            if text == "0":

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

                return

            if not text.isdigit():

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Введите число "
                        "от <b>1 до 10</b>."
                    )
                )

                return

            intensity = int(text)

            if intensity < 1 or intensity > 10:

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        "Значение должно быть "
                        "от <b>1 до 10</b>."
                    )
                )

                return

            from database.repositories.migraine_logs import migraine_logs

            migraine_logs.add_migraine(
                user_id,
                intensity
            )

            users.set_screen(
                user_id,
                "health"
            )

            api.send_message(
                chat_id=chat_id,
                text=(
                    "✅ <b>Мигрень записана</b>\n\n"
                    f"Сила: <b>{intensity}/10</b>\n\n"
                    "1 — 🩺 Давление\n"
                    "2 — 🧠 Мигрень\n\n"
                    "0 — назад"
                )
            )

            return

        # ==========================================
        # Мой день
        # ==========================================

        elif screen == "day":

            day_handler.handle(
                api,
                chat_id,
                user_id,
                first_name,
                text
            )

            return

        # ==========================================
        # Привычки
        # ==========================================

        elif screen in (
            "habits",
            "add_habit",
            "delete_habit"
        ):

            habits_handler.handle(
                api,
                chat_id,
                user_id,
                first_name,
                text,
                screen
            )

            return

        # ==========================================
        # Статистика
        # ==========================================

        elif screen in (
            "statistics",
            "statistics_day",
            "statistics_week",
            "statistics_month",
            "statistics_year"
        ):

            from app.commands import statistics
            from datetime import date

            if screen == "statistics":

                if text == "1":

                    users.set_screen(
                        user_id,
                        "statistics_day"
                    )

                    api.send_message(
                        chat_id=chat_id,
                        text=(
                            statistics.build_day_report(
                                user_id,
                                date.today()
                            )
                            + "\n\n0 — назад"
                        )
                    )

                    return

                if text == "2":

                    users.set_screen(
                        user_id,
                        "statistics_week"
                    )

                    api.send_message(
                        chat_id=chat_id,
                        text=(
                            statistics.build_week_report(
                                user_id,
                                date.today()
                            )
                            + "\n\n0 — назад"
                        )
                    )

                    return

                if text == "3":

                    users.set_screen(
                        user_id,
                        "statistics_month"
                    )

                    api.send_message(
                        chat_id=chat_id,
                        text=(
                            statistics.build_month_report(
                                user_id,
                                date.today()
                            )
                            + "\n\n0 — назад"
                        )
                    )

                    return

                if text == "4":

                    users.set_screen(
                        user_id,
                        "statistics_year"
                    )

                    api.send_message(
                        chat_id=chat_id,
                        text=(
                            statistics.build_year_report(
                                user_id,
                                date.today()
                            )
                            + "\n\n0 — назад"
                        )
                    )

                    return

                if text == "0":

                    users.set_screen(
                        user_id,
                        "menu"
                    )

                    from app.commands import menu

                    menu.execute(
                        api,
                        chat_id,
                        first_name
                    )

                    return

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

                return

            if text == "0":

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

                return

            if screen == "statistics_day":

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        statistics.build_day_report(
                            user_id,
                            date.today()
                        )
                        + "\n\n0 — назад"
                    )
                )

                return

            if screen == "statistics_week":

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        statistics.build_week_report(
                            user_id,
                            date.today()
                        )
                        + "\n\n0 — назад"
                    )
                )

                return

            if screen == "statistics_month":

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        statistics.build_month_report(
                            user_id,
                            date.today()
                        )
                        + "\n\n0 — назад"
                    )
                )

                return

            if screen == "statistics_year":

                api.send_message(
                    chat_id=chat_id,
                    text=(
                        statistics.build_year_report(
                            user_id,
                            date.today()
                        )
                        + "\n\n0 — назад"
                    )
                )

                return

        # ==========================================
        # Неизвестный экран
        # ==========================================

        print(
            f"WARNING: неизвестный screen='{screen}'"
        )

        users.set_screen(
            user_id,
            "menu"
        )

        from app.commands import menu

        menu.execute(
            api,
            chat_id,
            first_name
        )


dispatcher = Dispatcher()