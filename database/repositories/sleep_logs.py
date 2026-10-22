from datetime import date, datetime
from typing import Optional, Union

from database.db import Database


DateTimeValue = Union[datetime, str]


class SleepLogRepository:
    """Хранилище периодов сна пользователя.

    sleep_date сохраняет дату начала периода для совместимости со старыми
    записями. Для отображения завершённого сна за день используется дата
    пробуждения, а незавершённый период остаётся доступным независимо от даты.
    """

    def __init__(self):
        self.db = Database()
        # Отдельно храним отметку о бессонной ночи. Это не фиктивная
        # запись сна: человек может не спать ночью, а днём спать отдельно.
        self.db.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sleep_no_sleep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, report_date)
            )
            """
        )
        self.db.connection.commit()

    @staticmethod
    def _as_datetime(value: Optional[DateTimeValue]) -> Optional[datetime]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.isoformat(timespec="seconds")

    @staticmethod
    def _duration_text(started: datetime, wake_up: datetime) -> Optional[str]:
        seconds = (wake_up - started).total_seconds()
        if seconds < 0:
            return None
        total_minutes = int(seconds // 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours} ч {minutes} мин"

    def get_open_sleep(self, user_id):
        """Возвращает самый новый незавершённый период сна любой даты.

        Возвращаемая структура совместима с прежним кодом:
        (id, sleep_started_at, wake_up_at, sleep_date).
        """
        self.db.cursor.execute(
            """
            SELECT id, sleep_started_at, wake_up_at, sleep_date
            FROM sleep_logs
            WHERE user_id = ?
              AND sleep_started_at IS NOT NULL
              AND (wake_up_at IS NULL OR wake_up_at = '')
            ORDER BY sleep_started_at DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        return self.db.cursor.fetchone()

    def get_today(self, user_id):
        """Возвращает (id, start, wake) для активного сна или последнего сна,
        завершённого сегодня. Завершённая запись относится к дате пробуждения.
        """
        open_sleep = self.get_open_sleep(user_id)
        if open_sleep:
            return open_sleep[0], open_sleep[1], open_sleep[2]

        today = date.today().isoformat()
        self.db.cursor.execute(
            """
            SELECT id, sleep_started_at, wake_up_at
            FROM sleep_logs
            WHERE user_id = ?
              AND wake_up_at IS NOT NULL
              AND wake_up_at != ''
              AND date(wake_up_at) = ?
            ORDER BY wake_up_at DESC, id DESC
            LIMIT 1
            """,
            (user_id, today),
        )
        row = self.db.cursor.fetchone()
        if row:
            return row

        # Совместимость с историческими записями, в которых wake_up_at
        # мог быть пустым, но sleep_date совпадал с сегодняшней датой.
        self.db.cursor.execute(
            """
            SELECT id, sleep_started_at, wake_up_at
            FROM sleep_logs
            WHERE user_id = ? AND sleep_date = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, today),
        )
        return self.db.cursor.fetchone()

    def start_sleep(self, user_id, at: Optional[datetime] = None) -> bool:
        """Открывает новый период сна, не перезаписывая существующий.

        Возвращает False, если у пользователя уже есть незавершённый сон.
        """
        if at is None:
            at = datetime.now()
        if not isinstance(at, datetime):
            return False

        if self.get_open_sleep(user_id):
            return False

        self.db.cursor.execute(
            """
            INSERT INTO sleep_logs
                (user_id, sleep_date, sleep_started_at, wake_up_at)
            VALUES (?, ?, ?, NULL)
            """,
            (user_id, at.date().isoformat(), self._iso(at)),
        )
        self.db.connection.commit()
        return True

    def wake_up(self, user_id, at: Optional[datetime] = None) -> bool:
        """Закрывает текущий период сна, если время пробуждения позже начала."""
        if at is None:
            at = datetime.now()
        if not isinstance(at, datetime):
            return False

        existing = self.get_open_sleep(user_id)
        if not existing:
            return False

        started = self._as_datetime(existing[1])
        if started is None or at <= started:
            return False

        self.db.cursor.execute(
            """
            UPDATE sleep_logs
            SET wake_up_at = ?
            WHERE id = ? AND user_id = ?
              AND (wake_up_at IS NULL OR wake_up_at = '')
            """,
            (self._iso(at), existing[0], user_id),
        )
        self.db.connection.commit()
        return self.db.cursor.rowcount == 1

    def add_sleep(self, user_id, started_at: DateTimeValue, wake_up_at: DateTimeValue):
        """Добавляет завершённый период сна вручную.

        Возвращает ID новой записи или None, если даты некорректны.
        Допускает сон в любое время суток и переход через полночь.
        """
        started = self._as_datetime(started_at)
        wake_up = self._as_datetime(wake_up_at)
        if started is None or wake_up is None or wake_up <= started:
            return None

        self.db.cursor.execute(
            """
            INSERT INTO sleep_logs
                (user_id, sleep_date, sleep_started_at, wake_up_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                started.date().isoformat(),
                self._iso(started),
                self._iso(wake_up),
            ),
        )
        self.db.connection.commit()
        return self.db.cursor.lastrowid

    def get_sleep_by_id(self, user_id, sleep_id):
        """Возвращает запись только если она принадлежит этому пользователю."""
        self.db.cursor.execute(
            """
            SELECT id, sleep_date, sleep_started_at, wake_up_at
            FROM sleep_logs
            WHERE user_id = ? AND id = ?
            LIMIT 1
            """,
            (user_id, sleep_id),
        )
        return self.db.cursor.fetchone()

    def update_sleep(self, user_id, sleep_id, started_at: DateTimeValue,
                     wake_up_at: DateTimeValue) -> bool:
        """Изменяет период сна пользователя, проверяя даты и принадлежность."""
        started = self._as_datetime(started_at)
        wake_up = self._as_datetime(wake_up_at)
        if started is None or wake_up is None or wake_up <= started:
            return False

        self.db.cursor.execute(
            """
            UPDATE sleep_logs
            SET sleep_date = ?, sleep_started_at = ?, wake_up_at = ?
            WHERE user_id = ? AND id = ?
            """,
            (
                started.date().isoformat(),
                self._iso(started),
                self._iso(wake_up),
                user_id,
                sleep_id,
            ),
        )
        self.db.connection.commit()
        return self.db.cursor.rowcount == 1

    def get_recent_sleeps(self, user_id, limit=20):
        """Возвращает историю пользователя от новых записей к старым.

        Строки имеют формат (id, sleep_date, started_at, wake_up_at).
        Незавершённая запись также включается в список.
        """
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))

        self.db.cursor.execute(
            """
            SELECT id, sleep_date, sleep_started_at, wake_up_at
            FROM sleep_logs
            WHERE user_id = ?
            ORDER BY COALESCE(wake_up_at, sleep_started_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return self.db.cursor.fetchall()

    @staticmethod
    def _as_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if not value:
            return None
        text = str(value).strip()
        try:
            return date.fromisoformat(text)
        except ValueError:
            for fmt in ("%d.%m.%Y", "%d.%m.%y"):
                try:
                    return datetime.strptime(text, fmt).date()
                except ValueError:
                    pass
        return None

    def mark_no_sleep(self, user_id, report_date):
        """Mark that the night ending on report_date was spent without sleep."""
        parsed_date = self._as_date(report_date)
        if parsed_date is None:
            return False
        self.db.cursor.execute(
            """
            INSERT OR IGNORE INTO sleep_no_sleep_logs
                (user_id, report_date, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, parsed_date.isoformat(), datetime.now().isoformat(timespec="seconds")),
        )
        self.db.connection.commit()
        return self.db.cursor.rowcount == 1

    def remove_no_sleep(self, user_id, report_date):
        parsed_date = self._as_date(report_date)
        if parsed_date is None:
            return False
        self.db.cursor.execute(
            "DELETE FROM sleep_no_sleep_logs WHERE user_id = ? AND report_date = ?",
            (user_id, parsed_date.isoformat()),
        )
        self.db.connection.commit()
        return self.db.cursor.rowcount == 1

    def get_no_sleep_dates(self, user_id, start_date, end_date):
        start = self._as_date(start_date)
        end = self._as_date(end_date)
        if start is None or end is None or end < start:
            return []
        self.db.cursor.execute(
            """
            SELECT report_date
            FROM sleep_no_sleep_logs
            WHERE user_id = ? AND report_date BETWEEN ? AND ?
            ORDER BY report_date
            """,
            (user_id, start.isoformat(), end.isoformat()),
        )
        result = []
        for row in self.db.cursor.fetchall():
            parsed = self._as_date(row[0])
            if parsed is not None:
                result.append(parsed)
        return result

    def get_recent_no_sleep_dates(self, user_id, limit=10):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 50))
        self.db.cursor.execute(
            """
            SELECT report_date
            FROM sleep_no_sleep_logs
            WHERE user_id = ?
            ORDER BY report_date DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        result = []
        for row in self.db.cursor.fetchall():
            parsed = self._as_date(row[0])
            if parsed is not None:
                result.append(parsed)
        return result

    def get_today_info(self, user_id):
        row = self.get_today(user_id)
        if not row:
            return {"started": None, "wake_up": None, "duration": None}

        started = self._as_datetime(row[1])
        wake_up = self._as_datetime(row[2])
        duration = None

        if started and wake_up:
            duration = self._duration_text(started, wake_up)

        return {"started": started, "wake_up": wake_up, "duration": duration}


sleep_logs = SleepLogRepository()
