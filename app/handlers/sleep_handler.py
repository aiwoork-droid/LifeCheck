from datetime import date, datetime, timedelta

from app.commands import menu, today
from database.repositories.sleep_logs import sleep_logs
from database.repositories.users import users


TEMP_STARTED = "sleep_manual_started_at"
TEMP_MODE = "sleep_entry_mode"
TEMP_EDIT_ID = "sleep_edit_id"


def _button(text, payload):
    return {"type": "callback", "text": text, "payload": payload}


def _navigation_buttons(back_payload="nav:back"):
    return [[
        _button("⬅️ Назад", back_payload),
        _button("🏠 Главное меню", "nav:menu"),
    ]]


def _parse_datetime(value):
    value = (value or "").strip()
    formats = (
        "%d.%m.%Y %H:%M",
        "%d.%m.%y %H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%d.%m.%Y, %H:%M",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _format_dt(value):
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime("%d.%m.%Y %H:%M")
    except (TypeError, ValueError):
        return str(value)


def _duration(started, wake_up):
    try:
        start_dt = datetime.fromisoformat(str(started))
        wake_dt = datetime.fromisoformat(str(wake_up))
    except (TypeError, ValueError):
        return None

    minutes = int((wake_dt - start_dt).total_seconds() // 60)
    if minutes < 0:
        return None
    hours, remainder = divmod(minutes, 60)
    return f"{hours} ч {remainder} мин"


def _clear_manual_values(user_id):
    for key in (TEMP_STARTED, TEMP_MODE, TEMP_EDIT_ID):
        users.delete_temp_value(user_id, key)


def _show_menu(api, chat_id, user_id, notice=None):
    users.set_screen(user_id, "sleep_menu")
    open_sleep = sleep_logs.get_open_sleep(user_id)

    lines = ["😴 <b>Сон</b>", ""]
    if notice:
        lines.extend([notice, ""])

    if open_sleep:
        lines.extend([
            "🟣 <b>Сон ещё не завершён</b>",
            f"Начало: <b>{_format_dt(open_sleep[1])}</b>",
            "Когда проснётесь, нажмите «Проснулся».",
        ])
        action_buttons = [[_button("🌅 Проснулся", "sleep:wake")]]
    else:
        info = sleep_logs.get_today_info(user_id)
        if info.get("started") and info.get("wake_up"):
            lines.extend([
                "Последняя запись:",
                f"🌙 Начало: <b>{info['started'].strftime('%d.%m.%Y %H:%M')}</b>",
                f"🌅 Пробуждение: <b>{info['wake_up'].strftime('%d.%m.%Y %H:%M')}</b>",
                f"⏱ Продолжительность: <b>{info.get('duration') or '—'}</b>",
            ])
        else:
            lines.append("Сон пока не отмечен.")
        action_buttons = [[_button("🌙 Лёг спать", "sleep:start")]]

    lines.extend([
        "",
        "Автоматические отметки используют текущее время.",
        "Если забыли отметить сон или хотите исправить время — выберите ручную запись.",
    ])
    buttons = action_buttons + [
        [_button("✏️ Добавить или исправить", "sleep:edit")],
        [_button("🌙 Отметить бессонную ночь", "sleep:no_sleep")],
    ] + _navigation_buttons()

    api.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        buttons=buttons,
    )


def _show_edit_menu(api, chat_id, user_id):
    users.set_screen(user_id, "sleep_edit_menu")
    api.send_message(
        chat_id=chat_id,
        text=(
            "✏️ <b>Добавить или исправить сон</b>\n\n"
            "Выберите действие. Можно указать любое время суток "
            "и дату пробуждения, в том числе на следующий день."
        ),
        buttons=[
            [
                _button("➕ Добавить пропущенный сон", "sleep:add"),
                _button("📝 Исправить запись", "sleep:edit_existing"),
            ],
        ] + _navigation_buttons(),
    )


def _show_edit_picker(api, chat_id, user_id):
    records = sleep_logs.get_recent_sleeps(user_id, limit=8)
    users.set_screen(user_id, "sleep_edit_select")

    if not records:
        users.set_screen(user_id, "sleep_edit_menu")
        api.send_message(
            chat_id=chat_id,
            text=(
                "Пока нет записей сна для исправления.\n\n"
                "Можно добавить пропущенную запись вручную."
            ),
            buttons=[
                [_button("➕ Добавить пропущенный сон", "sleep:add")],
            ] + _navigation_buttons("sleep:edit_menu"),
        )
        return

    buttons = []
    lines = ["📝 <b>Какую запись исправить?</b>", ""]
    for row in records:
        sleep_id, _sleep_date, started, wake_up = row
        start_label = _format_dt(started)
        if wake_up:
            wake_label = _format_dt(wake_up)
            duration = _duration(started, wake_up)
            label = f"{start_label} → {wake_label}"
            if duration:
                label += f" ({duration})"
        else:
            label = f"{start_label} → ещё не завершён"
        lines.append(f"• {label}")
        button_label = f"{_format_dt(started)}"
        buttons.append([_button(button_label, f"sleep:select:{sleep_id}")])

    buttons += _navigation_buttons("sleep:edit_menu")
    api.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        buttons=buttons,
    )


def _parse_date(value):
    value = (value or "").strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _show_no_sleep_menu(api, chat_id, user_id):
    """Choose the morning date associated with a sleepless night."""
    users.set_screen(user_id, "sleep_no_sleep_menu")
    today = date.today()
    yesterday = today - timedelta(days=1)
    api.send_message(
        chat_id=chat_id,
        text=(
            "🌙 <b>Отметить бессонную ночь</b>\n\n"
            "Выберите утро, к которому относится ночь. Например, если не спали "
            "в ночь с 21 на 22 октября, выберите 22 октября.\n\n"
            "Такая отметка не мешает отдельно записать дневной сон."
        ),
        buttons=[
            [_button(f"🌙 Минувшая ночь ({today.strftime('%d.%m')})", f"sleep:no_sleep:mark:{today.isoformat()}")],
            [_button(f"🌙 Ночь перед ней ({yesterday.strftime('%d.%m')})", f"sleep:no_sleep:mark:{yesterday.isoformat()}")],
            [_button("📅 Указать другую дату", "sleep:no_sleep:custom")],
            [_button("🧹 Удалить отметку", "sleep:no_sleep:remove")],
        ] + _navigation_buttons(),
    )


def _show_no_sleep_remove_picker(api, chat_id, user_id):
    records = sleep_logs.get_recent_no_sleep_dates(user_id, limit=10)
    users.set_screen(user_id, "sleep_no_sleep_remove")
    if not records:
        api.send_message(
            chat_id=chat_id,
            text="Отметок о бессонных ночах пока нет.",
            buttons=_navigation_buttons("sleep:no_sleep"),
        )
        return

    buttons = [
        [_button(f"Удалить отметку за {day.strftime('%d.%m.%Y')}", f"sleep:no_sleep:remove:{day.isoformat()}")]
        for day in records
    ]
    buttons += _navigation_buttons("sleep:no_sleep")
    api.send_message(
        chat_id=chat_id,
        text="🧹 <b>Какую отметку удалить?</b>\n\nВыберите дату утра после бессонной ночи.",
        buttons=buttons,
    )


def _prompt_start(api, chat_id, user_id, *, mode="add", sleep_id=None, current_start=None):
    users.set_temp_value(user_id, TEMP_MODE, mode)
    if sleep_id is not None:
        users.set_temp_value(user_id, TEMP_EDIT_ID, sleep_id)
    else:
        users.delete_temp_value(user_id, TEMP_EDIT_ID)

    users.set_screen(user_id, "sleep_manual_start")
    lines = [
        "✏️ <b>Начало сна</b>",
        "",
        "Введите дату и время начала в формате:",
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>",
        "Например: <code>21.10.2026 22:30</code>.",
    ]
    if current_start:
        lines.extend(["", f"Текущее значение: <b>{_format_dt(current_start)}</b>"])
    api.send_message(
        chat_id=chat_id,
        text="\n".join(lines),
        buttons=_navigation_buttons("nav:back"),
    )


def _prompt_end(api, chat_id, user_id, started_text):
    users.set_screen(user_id, "sleep_manual_end")
    api.send_message(
        chat_id=chat_id,
        text=(
            "🌅 <b>Пробуждение</b>\n\n"
            f"Начало сна: <b>{_format_dt(started_text)}</b>\n\n"
            "Введите дату и время пробуждения в формате "
            "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>.\n"
            "Например: <code>22.10.2026 09:00</code>.\n\n"
            "Дата и время пробуждения должны быть позже начала сна."
        ),
        buttons=_navigation_buttons("sleep:back_to_start"),
    )


def _finish_action(api, chat_id, user_id, screen, notice):
    if screen == "sleep_menu":
        _show_menu(api, chat_id, user_id, notice=notice)
        return

    users.set_screen(user_id, "today")
    today.execute(api, chat_id, user_id, notice=notice)


def _start_sleep(api, chat_id, user_id, screen):
    now = datetime.now()
    if sleep_logs.start_sleep(user_id, at=now):
        notice = f"✅ Начало сна записано: <b>{now.strftime('%d.%m.%Y %H:%M')}</b>"
    else:
        opened = sleep_logs.get_open_sleep(user_id)
        started = _format_dt(opened[1]) if opened else "—"
        notice = (
            "⚠️ Незавершённый сон уже есть. "
            f"Начало: <b>{started}</b>. Время не изменено."
        )
    _finish_action(api, chat_id, user_id, screen, notice)


def _wake_sleep(api, chat_id, user_id, screen):
    now = datetime.now()
    opened = sleep_logs.get_open_sleep(user_id)
    if not opened:
        notice = (
            "⚠️ Активный сон не найден. "
            "Если забыли отметить начало, нажмите «Добавить или исправить сон»."
        )
        _finish_action(api, chat_id, user_id, screen, notice)
        return

    if not sleep_logs.wake_up(user_id, at=now):
        notice = "⚠️ Не удалось завершить сон. Проверьте дату и время начала."
        _finish_action(api, chat_id, user_id, screen, notice)
        return

    duration = _duration(opened[1], now.isoformat()) or "—"
    notice = (
        "✅ <b>Пробуждение записано</b>\n"
        f"Начало: {_format_dt(opened[1])}\n"
        f"Окончание: <b>{now.strftime('%d.%m.%Y %H:%M')}</b>\n"
        f"Продолжительность: <b>{duration}</b>"
    )
    _finish_action(api, chat_id, user_id, screen, notice)


def _handle_back(api, chat_id, user_id, first_name, screen):
    if screen == "sleep_menu":
        users.set_screen(user_id, "today")
        today.execute(api, chat_id, user_id)
        return

    if screen == "sleep_edit_menu":
        _show_menu(api, chat_id, user_id)
        return

    if screen == "sleep_edit_select":
        _show_edit_menu(api, chat_id, user_id)
        return

    if screen in ("sleep_no_sleep_menu", "sleep_no_sleep_remove"):
        _show_menu(api, chat_id, user_id)
        return

    if screen == "sleep_no_sleep_date":
        _show_no_sleep_menu(api, chat_id, user_id)
        return

    if screen == "sleep_manual_end":
        started_text = users.get_temp_value(user_id, TEMP_STARTED)
        _prompt_start(
            api,
            chat_id,
            user_id,
            mode=users.get_temp_value(user_id, TEMP_MODE) or "add",
            sleep_id=users.get_temp_value(user_id, TEMP_EDIT_ID),
            current_start=started_text,
        )
        return

    if screen == "sleep_manual_start":
        mode = users.get_temp_value(user_id, TEMP_MODE)
        sleep_id = users.get_temp_value(user_id, TEMP_EDIT_ID)
        users.delete_temp_value(user_id, TEMP_STARTED)
        if mode == "edit" and sleep_id is not None:
            _show_edit_picker(api, chat_id, user_id)
        else:
            _show_edit_menu(api, chat_id, user_id)
        return

    users.set_screen(user_id, "today")
    today.execute(api, chat_id, user_id)


def handle(api, chat_id, user_id, first_name, text, screen):
    """Обрабатывает меню сна, автоматические отметки и ручное редактирование."""
    text = (text or "").strip()

    if text == "nav:menu":
        _clear_manual_values(user_id)
        users.set_screen(user_id, "menu")
        menu.execute(api, chat_id, first_name)
        return

    if text == "nav:back":
        _handle_back(api, chat_id, user_id, first_name, screen)
        return

    if text == "sleep:open":
        _show_menu(api, chat_id, user_id)
        return

    if text == "sleep:edit_menu":
        _show_edit_menu(api, chat_id, user_id)
        return

    if text == "sleep:edit":
        _show_edit_menu(api, chat_id, user_id)
        return

    if text == "sleep:no_sleep":
        _show_no_sleep_menu(api, chat_id, user_id)
        return

    if text == "sleep:no_sleep:custom":
        users.set_screen(user_id, "sleep_no_sleep_date")
        api.send_message(
            chat_id=chat_id,
            text=(
                "📅 <b>Дата бессонной ночи</b>\n\n"
                "Введите дату утра после этой ночи в формате "
                "<code>ДД.ММ.ГГГГ</code>.\n"
                "Например: <code>22.10.2026</code>."
            ),
            buttons=_navigation_buttons("nav:back"),
        )
        return

    if text == "sleep:no_sleep:remove":
        _show_no_sleep_remove_picker(api, chat_id, user_id)
        return

    if text.startswith("sleep:no_sleep:mark:"):
        report_date = _parse_date(text.rsplit(":", 1)[1])
        if report_date is None:
            _show_no_sleep_menu(api, chat_id, user_id)
            return
        marked = sleep_logs.mark_no_sleep(user_id, report_date)
        notice = (
            f"✅ Отметка «не спал ночью» сохранена за {report_date.strftime('%d.%m.%Y')}."
            if marked else
            f"ℹ️ Отметка за {report_date.strftime('%d.%m.%Y')} уже существует."
        )
        _show_menu(api, chat_id, user_id, notice=notice)
        return

    if text.startswith("sleep:no_sleep:remove:"):
        report_date = _parse_date(text.rsplit(":", 1)[1])
        removed = report_date is not None and sleep_logs.remove_no_sleep(user_id, report_date)
        notice = (
            f"✅ Отметка за {report_date.strftime('%d.%m.%Y')} удалена."
            if removed else "Отметка не найдена или уже удалена."
        )
        _show_menu(api, chat_id, user_id, notice=notice)
        return

    if text == "sleep:back_to_start":
        started_text = users.get_temp_value(user_id, TEMP_STARTED)
        _prompt_start(
            api,
            chat_id,
            user_id,
            mode=users.get_temp_value(user_id, TEMP_MODE) or "add",
            sleep_id=users.get_temp_value(user_id, TEMP_EDIT_ID),
            current_start=started_text,
        )
        return

    if text == "sleep:start":
        if screen not in ("today", "sleep_menu"):
            api.send_message(
                chat_id=chat_id,
                text="Сначала завершите или отмените текущую форму добавления/исправления сна.",
                buttons=_navigation_buttons("nav:back"),
            )
            return
        _start_sleep(api, chat_id, user_id, screen)
        return

    if text == "sleep:wake":
        if screen not in ("today", "sleep_menu"):
            api.send_message(
                chat_id=chat_id,
                text="Сначала завершите или отмените текущую форму добавления/исправления сна.",
                buttons=_navigation_buttons("nav:back"),
            )
            return
        _wake_sleep(api, chat_id, user_id, screen)
        return

    if screen == "sleep_no_sleep_date":
        report_date = _parse_date(text)
        if report_date is None:
            api.send_message(
                chat_id=chat_id,
                text="Не удалось распознать дату. Введите, например: <code>22.10.2026</code>.",
                buttons=_navigation_buttons("nav:back"),
            )
            return
        marked = sleep_logs.mark_no_sleep(user_id, report_date)
        notice = (
            f"✅ Отметка «не спал ночью» сохранена за {report_date.strftime('%d.%m.%Y')}."
            if marked else
            f"ℹ️ Отметка за {report_date.strftime('%d.%m.%Y')} уже существует."
        )
        _show_menu(api, chat_id, user_id, notice=notice)
        return

    if screen == "sleep_manual_start":
        started = _parse_datetime(text)
        if started is None:
            api.send_message(
                chat_id=chat_id,
                text=(
                    "Не удалось распознать дату и время.\n"
                    "Введите, например: <code>21.10.2026 22:30</code>."
                ),
                buttons=_navigation_buttons("sleep:edit_menu"),
            )
            return

        users.set_temp_value(user_id, TEMP_STARTED, started.isoformat(timespec="seconds"))
        _prompt_end(api, chat_id, user_id, started.isoformat(timespec="seconds"))
        return

    if screen == "sleep_manual_end":
        wake_up = _parse_datetime(text)
        started_text = users.get_temp_value(user_id, TEMP_STARTED)
        try:
            started = datetime.fromisoformat(str(started_text))
        except (TypeError, ValueError):
            _prompt_start(
                api,
                chat_id,
                user_id,
                mode=users.get_temp_value(user_id, TEMP_MODE) or "add",
                sleep_id=users.get_temp_value(user_id, TEMP_EDIT_ID),
            )
            return

        if wake_up is None or wake_up <= started:
            api.send_message(
                chat_id=chat_id,
                text=(
                    "Дата и время пробуждения указаны неверно.\n"
                    "Они должны быть позже начала сна.\n\n"
                    "Введите, например: <code>22.10.2026 09:00</code>."
                ),
                buttons=_navigation_buttons("sleep:back_to_start"),
            )
            return

        mode = users.get_temp_value(user_id, TEMP_MODE) or "add"
        edit_id = users.get_temp_value(user_id, TEMP_EDIT_ID)
        if mode == "edit" and edit_id is not None:
            saved = sleep_logs.update_sleep(
                user_id,
                int(edit_id),
                started,
                wake_up,
            )
            action = "исправлена" if saved else "не найдена; возможно, она уже удалена"
        else:
            saved_id = sleep_logs.add_sleep(user_id, started, wake_up)
            saved = saved_id is not None
            action = "добавлена" if saved else "не удалось сохранить"

        if saved:
            duration = _duration(started.isoformat(), wake_up.isoformat()) or "—"
            notice = (
                "✅ <b>Запись сна сохранена</b>\n"
                f"{started.strftime('%d.%m.%Y %H:%M')} → "
                f"{wake_up.strftime('%d.%m.%Y %H:%M')}\n"
                f"Продолжительность: <b>{duration}</b>"
            )
        else:
            notice = f"⚠️ Запись {action}. Попробуйте ещё раз."

        _clear_manual_values(user_id)
        _show_menu(api, chat_id, user_id, notice=notice)
        return

    if screen == "sleep_edit_select" and text.startswith("sleep:select:"):
        try:
            sleep_id = int(text.rsplit(":", 1)[1])
        except (ValueError, IndexError):
            _show_edit_picker(api, chat_id, user_id)
            return

        row = sleep_logs.get_sleep_by_id(user_id, sleep_id)
        if not row:
            _show_edit_picker(api, chat_id, user_id)
            return
        _prompt_start(
            api,
            chat_id,
            user_id,
            mode="edit",
            sleep_id=sleep_id,
            current_start=row[2],
        )
        return

    if screen == "sleep_menu":
        _show_menu(api, chat_id, user_id)
        return

    if screen == "sleep_edit_menu":
        if text == "sleep:add":
            users.delete_temp_value(user_id, TEMP_STARTED)
            _prompt_start(api, chat_id, user_id, mode="add")
            return
        if text == "sleep:edit_existing":
            _show_edit_picker(api, chat_id, user_id)
            return
        _show_edit_menu(api, chat_id, user_id)
        return

    if screen == "sleep_edit_select":
        if text == "sleep:edit_menu":
            _show_edit_menu(api, chat_id, user_id)
        else:
            _show_edit_picker(api, chat_id, user_id)
        return

    _show_menu(api, chat_id, user_id)
