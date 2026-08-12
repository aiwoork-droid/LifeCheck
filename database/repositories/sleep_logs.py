from datetime import date, datetime, timedelta

from database.db import Database


class SleepLogRepository:

    def __init__(self):

        self.db = Database()

    # =================================================
    # Получить сегодняшнюю запись
    # =================================================

    def get_today(self, user_id):

        self.db.cursor.execute(
            """
            SELECT
                id,
                sleep_started_at,
                wake_up_at
            FROM sleep_logs
            WHERE
                user_id=?
                AND sleep_date=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        return self.db.cursor.fetchone()

    # =================================================
    # Начать сон
    # =================================================

    def start_sleep(self, user_id):

        existing = self.get_today(user_id)

        # Если сегодня уже есть активная запись,
        # второй раз сон не начинаем.

        if existing and existing[1] and not existing[2]:
            return False

        now = datetime.now()

        self.db.cursor.execute(
            """
            INSERT INTO sleep_logs
            (
                user_id,
                sleep_date,
                sleep_started_at,
                wake_up_at
            )
            VALUES (?, ?, ?, NULL)
            """,
            (
                user_id,
                date.today().isoformat(),
                now.isoformat(timespec="seconds")
            )
        )

        self.db.connection.commit()

        return True

    # =================================================
    # Проснуться
    # =================================================

    def wake_up(self, user_id):

        existing = self.get_today(user_id)

        if not existing:
            return False

        if not existing[1]:
            return False

        if existing[2]:
            return False

        now = datetime.now()

        self.db.cursor.execute(
            """
            UPDATE sleep_logs
            SET wake_up_at=?
            WHERE id=?
            """,
            (
                now.isoformat(timespec="seconds"),
                existing[0]
            )
        )

        self.db.connection.commit()

        return True

    # =================================================
    # Получить информацию о сне
    # =================================================

    def get_today_info(self, user_id):

        row = self.get_today(user_id)

        if not row:
            return {
                "started": None,
                "wake_up": None,
                "duration": None
            }

        started = None
        wake_up = None
        duration = None

        try:

            if row[1]:
                started = datetime.fromisoformat(
                    row[1]
                )

            if row[2]:
                wake_up = datetime.fromisoformat(
                    row[2]
                )

        except Exception:

            return {
                "started": None,
                "wake_up": None,
                "duration": None
            }

        if started and wake_up:

            difference = wake_up - started

            total_minutes = int(
                difference.total_seconds() / 60
            )

            hours = total_minutes // 60
            minutes = total_minutes % 60

            duration = (
                f"{hours} ч {minutes} мин"
            )

        return {
            "started": started,
            "wake_up": wake_up,
            "duration": duration
        }


sleep_logs = SleepLogRepository()