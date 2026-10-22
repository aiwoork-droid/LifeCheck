from app.handlers import menu_handler
from app.handlers import day_handler
from app.handlers import habits_handler
from app.handlers import today_handler

from database.repositories.users import users
from database.repositories.blood_pressure_logs import blood_pressure_logs
from database.repositories.blood_sugar_logs import blood_sugar_logs


def _button(label, payload):
    return {"type": "callback", "text": label, "payload": payload}


def _nav_buttons(back_payload="nav:back"):
    return [[
        _button("⬅️ Назад", back_payload),
        _button("🏠 Главное меню", "nav:menu"),
    ]]


def _clear_health_temp(user_id):
    for key in (
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
        "blood_sugar_meal",
    ):
        users.delete_temp_value(user_id, key)


def _send_health_menu(api, chat_id, notice=None):
    lines = ["❤️ <b>Здоровье</b>", "", "Выберите раздел:"]
    if notice:
        lines = ["❤️ <b>Здоровье</b>", "", notice, "", "Выберите раздел:"]
    api.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        buttons=[
            [
                _button("🩺 Давление", "health:pressure"),
                _button("🧠 Мигрень", "health:migraine"),
            ],
            [_button("🩸 Сахар", "health:sugar")],
        ] + _nav_buttons(),
    )


def _send_pressure_menu(api, chat_id, notice=None):
    lines = ["🩺 <b>Давление</b>", "", "Выберите действие:"]
    if notice:
        lines = ["🩺 <b>Давление</b>", "", notice, "", "Выберите действие:"]
    api.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        buttons=[
            [
                _button("➕ Новое измерение", "pressure:new"),
                _button("📅 Сегодня", "pressure:today"),
            ],
            [_button("🗑 Удалить последнее", "pressure:delete")],
        ] + _nav_buttons(),
    )


def _send_sugar_menu(api, chat_id, notice=None):
    lines = ["🩸 <b>Сахар в крови</b>", "", "Выберите действие:"]
    if notice:
        lines = ["🩸 <b>Сахар в крови</b>", "", notice, "", "Выберите действие:"]
    api.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        buttons=[
            [
                _button("➕ Новое измерение", "sugar:new"),
                _button("📅 Сегодня", "sugar:today"),
            ],
            [_button("🗑 Удалить последнее", "sugar:delete")],
        ] + _nav_buttons(),
    )


def _send_meal_menu(api, chat_id):
    api.send_message(
        chat_id=chat_id,
        text="🩸 <b>Когда измеряли сахар?</b>\n\nВыберите контекст измерения:",
        buttons=[
            [
                _button("До еды", "sugar:meal:before"),
                _button("После еды", "sugar:meal:after"),
            ],
            [_button("Между приёмами пищи · 2 ч", "sugar:meal:between")],
        ] + _nav_buttons(),
    )


def _send_pressure_prompt(api, chat_id, text):
    api.send_message(
        chat_id=chat_id,
        text=text,
        buttons=_nav_buttons(),
    )


def _send_sugar_prompt(api, chat_id, text):
    api.send_message(
        chat_id=chat_id,
        text=text,
        buttons=_nav_buttons(),
    )


def _resume_health_input(api, chat_id, user_id, screen):
    if screen == "blood_pressure_systolic":
        current = users.get_temp_value(user_id, "blood_pressure_systolic")
        current_text = f"\nТекущее значение: <b>{current}</b>." if current is not None else ""
        _send_pressure_prompt(
            api, chat_id,
            "🩺 <b>Верхнее давление</b>\n\nВведите верхнее давление." + current_text + "\n\nНапример: <b>120</b>",
        )
        return

    if screen == "blood_pressure_diastolic":
        systolic = users.get_temp_value(user_id, "blood_pressure_systolic")
        _send_pressure_prompt(
            api, chat_id,
            f"🩺 Верхнее давление: <b>{systolic or '—'}</b>\n\nВведите нижнее давление.\nНапример: <b>80</b>",
        )
        return

    if screen == "blood_pressure_pulse":
        systolic = users.get_temp_value(user_id, "blood_pressure_systolic")
        diastolic = users.get_temp_value(user_id, "blood_pressure_diastolic")
        _send_pressure_prompt(
            api, chat_id,
            f"🩺 Давление: <b>{systolic or '—'}/{diastolic or '—'}</b>\n\nВведите пульс.\nНапример: <b>72</b>",
        )
        return

    if screen == "blood_sugar_value":
        meal = users.get_temp_value(user_id, "blood_sugar_meal")
        meal_label = blood_sugar_logs.MEAL_LABELS.get(meal, meal or "контекст не указан")
        _send_sugar_prompt(
            api, chat_id,
            f"🩸 <b>Введите уровень сахара</b>\n\nКонтекст: {meal_label}.\nНапример: <b>5.6</b> или <b>5,6</b> ммоль/л.",
        )
        return


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
        # Сон: callback-кнопки и ввод ручной записи
        # ==========================================

        if text.startswith("sleep:") or screen.startswith("sleep_"):

            from app.handlers import sleep_handler

            sleep_handler.handle(
                api,
                chat_id,
                user_id,
                first_name,
                text,
                screen
            )

            return

        # Предупреждаем перед выходом из незавершённого измерения.
        pending_screens = {
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "blood_pressure_pulse",
            "blood_sugar_value",
        }
        if screen == "health_exit_confirm":
            if text in ("health:exit_confirm", "nav:menu"):
                _clear_health_temp(user_id)
                users.delete_temp_value(user_id, "health_exit_previous_screen")
                users.set_screen(user_id, "menu")
                from app.commands import menu
                menu.execute(api, chat_id, first_name)
                return
            if text in ("health:exit_continue", "nav:back"):
                previous_screen = users.get_temp_value(user_id, "health_exit_previous_screen")
                users.delete_temp_value(user_id, "health_exit_previous_screen")
                if previous_screen not in pending_screens:
                    previous_screen = "blood_pressure_systolic"
                users.set_screen(user_id, previous_screen)
                _resume_health_input(api, chat_id, user_id, previous_screen)
                return
            api.send_message(
                chat_id=chat_id,
                text="Есть незавершённое измерение. Что сделать?",
                buttons=[[
                    _button("↩️ Продолжить ввод", "health:exit_continue"),
                    _button("🏠 Отменить и выйти", "health:exit_confirm"),
                ]],
            )
            return

        if text == "nav:menu" and screen in pending_screens:
            users.set_temp_value(user_id, "health_exit_previous_screen", screen)
            users.set_screen(user_id, "health_exit_confirm")
            api.send_message(
                chat_id=chat_id,
                text=(
                    "⚠️ <b>Измерение ещё не завершено</b>\n\n"
                    "Если выйти сейчас, введённые значения не будут сохранены. "
                    "Продолжить ввод или отменить измерение?"
                ),
                buttons=[[
                    _button("↩️ Продолжить ввод", "health:exit_continue"),
                    _button("🏠 Отменить и выйти", "health:exit_confirm"),
                ]],
            )
            return

        # Главное меню доступно из любого текущего раздела.
        if text == "nav:menu":
            _clear_health_temp(user_id)
            users.set_screen(user_id, "menu")
            from app.commands import menu
            menu.execute(api, chat_id, first_name)
            return

        # Общая навигация для экранов здоровья.
        # При переходе назад на шаг ввода значения сохраняются, если это возможно.
        if text == "nav:back":
            if screen in ("today", "health"):
                _clear_health_temp(user_id)
                users.set_screen(user_id, "menu")
                from app.commands import menu
                menu.execute(api, chat_id, first_name)
                return

            if screen in ("health_pressure", "health_sugar", "migraine_intensity"):
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health")
                _send_health_menu(api, chat_id)
                return

            if screen == "blood_pressure_systolic":
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id)
                return

            if screen == "blood_pressure_diastolic":
                systolic = users.get_temp_value(user_id, "blood_pressure_systolic")
                users.set_screen(user_id, "blood_pressure_systolic")
                current = f"\nТекущее значение: <b>{systolic}</b>." if systolic is not None else ""
                _send_pressure_prompt(
                    api, chat_id,
                    "🩺 <b>Верхнее давление</b>\n\nВведите верхнее давление."
                    + current + "\n\nНапример: <b>120</b>"
                )
                return

            if screen == "blood_pressure_pulse":
                systolic = users.get_temp_value(user_id, "blood_pressure_systolic")
                diastolic = users.get_temp_value(user_id, "blood_pressure_diastolic")
                users.set_screen(user_id, "blood_pressure_diastolic")
                current = f"\nТекущее значение: <b>{diastolic}</b>." if diastolic is not None else ""
                _send_pressure_prompt(
                    api, chat_id,
                    f"🩺 Давление: <b>{systolic or '—'}/{diastolic or '—'}</b>\n\n"
                    "Введите нижнее давление." + current + "\n\nНапример: <b>80</b>"
                )
                return

            if screen == "blood_sugar_meal":
                users.set_screen(user_id, "health_sugar")
                _send_sugar_menu(api, chat_id)
                return

            if screen == "blood_sugar_value":
                users.set_screen(user_id, "blood_sugar_meal")
                _send_meal_menu(api, chat_id)
                return


        # ==========================================
        # Главное меню
        # ==========================================

        if screen == "menu":

            # Первый вход в здоровье из главного меню тоже сразу показывает кнопки.
            if text in ("4", "health:open"):
                users.set_screen(user_id, "health")
                _send_health_menu(api, chat_id)
                return

            menu_handler.handle(
                api,
                chat_id,
                user_id,
                first_name,
                text
            )

            return

        # ==========================================
        # Здоровье — внутреннее меню на кнопках
        # ==========================================

        elif screen == "health":

            if text in ("0", "nav:back"):
                users.set_screen(user_id, "menu")
                from app.commands import menu
                menu.execute(api, chat_id, first_name)
                return

            if text in ("health:pressure", "1"):
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id)
                return

            if text in ("health:migraine", "2"):
                users.set_screen(user_id, "migraine_intensity")
                _send_pressure_prompt(
                    api, chat_id,
                    "🧠 <b>Мигрень</b>\n\nУкажите силу боли от <b>1 до 10</b>.\n\n"
                    "1 — очень слабо\n10 — очень сильно\n\nВведите число.",
                )
                return

            if text in ("health:sugar", "3"):
                users.set_screen(user_id, "health_sugar")
                _send_sugar_menu(api, chat_id)
                return

            _send_health_menu(api, chat_id)
            return

        # ==========================================
        # Раздел давления
        # ==========================================

        elif screen == "health_pressure":
            if text in ("0", "health:back"):
                users.set_screen(user_id, "health")
                _send_health_menu(api, chat_id)
                return

            if text in ("pressure:new", "1"):
                users.set_screen(user_id, "blood_pressure_systolic")
                users.delete_temp_value(user_id, "blood_pressure_systolic")
                users.delete_temp_value(user_id, "blood_pressure_diastolic")
                _send_pressure_prompt(
                    api, chat_id,
                    "🩺 <b>Новое измерение</b>\n\nВведите верхнее давление.\n\nНапример: <b>120</b>\n\nМожно ввести число сообщением.",
                )
                return

            if text in ("pressure:today", "2"):
                measurements = blood_pressure_logs.get_today_measurements(user_id)
                if not measurements:
                    result = "🩺 <b>Давление сегодня</b>\n\nИзмерений пока нет."
                else:
                    result_lines = ["🩺 <b>Давление сегодня</b>", ""]
                    for measurement in measurements:
                        time_text = measurement.get("time") or "--:--"
                        result_lines.append(
                            f"{time_text} — {measurement['systolic']}/{measurement['diastolic']}, "
                            f"пульс {measurement['pulse']}"
                        )
                    result = "\n".join(result_lines)
                api.send_message(
                    chat_id=chat_id, text=result,
                    buttons=[[ _button("🩺 К действиям с давлением", "health:pressure") ]] + _nav_buttons(),
                )
                return

            if text in ("pressure:delete", "3"):
                removed = blood_pressure_logs.remove_last_measurement(user_id)
                notice = "✅ Последнее измерение удалено." if removed else "Сегодня нет измерений для удаления."
                _send_pressure_menu(api, chat_id, notice=notice)
                return

            _send_pressure_menu(api, chat_id)
            return

        # ==========================================
        # Ввод верхнего / нижнего давления и пульса
        # ==========================================

        elif screen == "blood_pressure_systolic":
            if text == "0":
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id, notice="Измерение отменено.")
                return

            if not text.isdigit():
                _send_pressure_prompt(api, chat_id, "Введите верхнее давление числом.\nНапример: <b>120</b>")
                return

            systolic = int(text)
            if systolic < 50 or systolic > 250:
                _send_pressure_prompt(api, chat_id, "Значение выглядит необычно.\nВведите верхнее давление от 50 до 250.")
                return

            users.set_temp_value(user_id, "blood_pressure_systolic", systolic)
            users.set_screen(user_id, "blood_pressure_diastolic")
            _send_pressure_prompt(
                api, chat_id,
                f"🩺 Верхнее давление: <b>{systolic}</b>\n\nВведите нижнее давление.\nНапример: <b>80</b>",
            )
            return

        elif screen == "blood_pressure_diastolic":
            if text == "0":
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id, notice="Измерение отменено.")
                return

            if not text.isdigit():
                _send_pressure_prompt(api, chat_id, "Введите нижнее давление числом.\nНапример: <b>80</b>")
                return

            diastolic = int(text)
            if diastolic < 30 or diastolic > 150:
                _send_pressure_prompt(api, chat_id, "Значение выглядит необычно.\nВведите нижнее давление от 30 до 150.")
                return

            systolic = users.get_temp_value(user_id, "blood_pressure_systolic")
            if systolic is None:
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id, notice="Начните измерение заново.")
                return

            users.set_temp_value(user_id, "blood_pressure_diastolic", diastolic)
            users.set_screen(user_id, "blood_pressure_pulse")
            _send_pressure_prompt(
                api, chat_id,
                f"🩺 Давление: <b>{systolic}/{diastolic}</b>\n\nВведите пульс.\nНапример: <b>72</b>",
            )
            return

        elif screen == "blood_pressure_pulse":
            if text == "0":
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id, notice="Измерение отменено.")
                return

            if not text.isdigit():
                _send_pressure_prompt(api, chat_id, "Введите пульс числом.\nНапример: <b>72</b>")
                return

            pulse = int(text)
            if pulse < 30 or pulse > 220:
                _send_pressure_prompt(api, chat_id, "Значение выглядит необычно.\nВведите пульс от 30 до 220.")
                return

            systolic = users.get_temp_value(user_id, "blood_pressure_systolic")
            diastolic = users.get_temp_value(user_id, "blood_pressure_diastolic")
            if systolic is None or diastolic is None:
                _clear_health_temp(user_id)
                users.set_screen(user_id, "health_pressure")
                _send_pressure_menu(api, chat_id, notice="Начните измерение заново.")
                return

            blood_pressure_logs.add_measurement(user_id, systolic, diastolic, pulse)
            _clear_health_temp(user_id)
            users.set_screen(user_id, "health_pressure")
            _send_pressure_menu(
                api, chat_id,
                notice=(
                    "✅ <b>Измерение сохранено</b>\n"
                    f"🩺 {systolic}/{diastolic}\n❤️ Пульс: {pulse}\n"
                    "Время записано автоматически."
                ),
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
        # Сахар в крови — все варианты выбора кнопками
        # ==========================================

        elif screen == "health_sugar":
            if text in ("0", "health:back"):
                users.delete_temp_value(user_id, "blood_sugar_meal")
                users.set_screen(user_id, "health")
                _send_health_menu(api, chat_id)
                return

            if text in ("sugar:new", "1"):
                users.set_screen(user_id, "blood_sugar_meal")
                _send_meal_menu(api, chat_id)
                return

            if text in ("sugar:today", "2"):
                measurements = blood_sugar_logs.get_today_measurements(user_id)
                if not measurements:
                    result = "🩸 <b>Сахар сегодня</b>\n\nИзмерений пока нет."
                else:
                    lines = ["🩸 <b>Сахар сегодня</b>", ""]
                    for measurement in measurements:
                        time_text = measurement.get("time") or "--:--"
                        lines.append(
                            f"{time_text} — <b>{measurement['value']}</b> ммоль/л "
                            f"({measurement.get('meal_label') or 'контекст не указан'})"
                        )
                    result = "\n\n".join(lines)
                api.send_message(
                    chat_id=chat_id, text=result,
                    buttons=[[_button("🩸 К действиям с сахаром", "health:sugar")]] + _nav_buttons(),
                )
                return

            if text in ("sugar:delete", "3"):
                ok = blood_sugar_logs.remove_last_measurement(user_id)
                notice = "✅ Последнее измерение удалено." if ok else "Нечего удалять — записей сегодня нет."
                _send_sugar_menu(api, chat_id, notice=notice)
                return

            _send_sugar_menu(api, chat_id)
            return

        elif screen == "blood_sugar_meal":
            if text == "0":
                users.set_screen(user_id, "health_sugar")
                _send_sugar_menu(api, chat_id, notice="Добавление измерения отменено.")
                return

            meal_map = {
                "sugar:meal:before": "before",
                "sugar:meal:after": "after",
                "sugar:meal:between": "between",
                "1": "before",
                "2": "after",
                "3": "between",
            }
            meal = meal_map.get(text)
            if meal is None:
                _send_meal_menu(api, chat_id)
                return

            users.set_temp_value(user_id, "blood_sugar_meal", meal)
            users.set_screen(user_id, "blood_sugar_value")
            _send_sugar_prompt(
                api, chat_id,
                "🩸 <b>Введите уровень сахара</b>\n\nНапример: <b>5.6</b> или <b>5,6</b> ммоль/л.",
            )
            return

        elif screen == "blood_sugar_value":
            if text == "0":
                users.delete_temp_value(user_id, "blood_sugar_meal")
                users.set_screen(user_id, "health_sugar")
                _send_sugar_menu(api, chat_id, notice="Добавление измерения отменено.")
                return

            meal = users.get_temp_value(user_id, "blood_sugar_meal")
            if not meal:
                users.set_screen(user_id, "blood_sugar_meal")
                _send_meal_menu(api, chat_id)
                return

            raw = text.replace(",", ".").strip()
            try:
                value = float(raw)
            except ValueError:
                _send_sugar_prompt(api, chat_id, "Введите число, например <b>5.6</b> или <b>5,6</b>.")
                return

            if value < 1.0 or value > 40.0:
                _send_sugar_prompt(api, chat_id, "Значение выглядит необычно. Введите сахар от <b>1.0</b> до <b>40.0</b> ммоль/л.")
                return

            ok = blood_sugar_logs.add_measurement(user_id, value, meal)
            users.delete_temp_value(user_id, "blood_sugar_meal")
            users.set_screen(user_id, "health_sugar")
            if ok:
                label = blood_sugar_logs.MEAL_LABELS.get(meal, meal)
                _send_sugar_menu(
                    api, chat_id,
                    notice=f"✅ <b>Измерение сохранено</b>\n{value:g} ммоль/л\n({label})",
                )
            else:
                _send_sugar_menu(api, chat_id, notice="⚠️ Не удалось сохранить измерение. Попробуйте снова.")
            return

        # ==========================================
        # Мигрень
        # ==========================================

        elif screen == "migraine_intensity":
            if text == "0":
                users.set_screen(user_id, "health")
                _send_health_menu(api, chat_id, notice="Отметка мигрени отменена.")
                return

            if not text.isdigit():
                _send_pressure_prompt(api, chat_id, "Введите силу боли числом от <b>1 до 10</b>.")
                return

            intensity = int(text)
            if intensity < 1 or intensity > 10:
                _send_pressure_prompt(api, chat_id, "Значение должно быть от <b>1 до 10</b>.")
                return

            from database.repositories.migraine_logs import migraine_logs
            migraine_logs.add_migraine(user_id, intensity)
            users.set_screen(user_id, "health")
            _send_health_menu(api, chat_id, notice=f"✅ Мигрень записана. Сила: <b>{intensity}/10</b>.")
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
