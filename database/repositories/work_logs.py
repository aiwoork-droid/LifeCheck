from datetime import date, datetime

from database.db import Database


class WorkLogRepository:

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
                work_started_at,
                work_finished_at
            FROM work_logs
            WHERE
                user_id=?
                AND work_date=?
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
    # Начать работу
    # =================================================

    def start_work(self, user_id):

        existing = self.get_today(user_id)

        if existing and existing[1] and not existing[2]:

            return False

        now = datetime.now()

        self.db.cursor.execute(
            """
            INSERT INTO work_logs
            (
                user_id,
                work_date,
                work_started_at,
                work_finished_at
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
    # Закончить работу
    # =================================================

    def finish_work(self, user_id):

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
            UPDATE work_logs
            SET work_finished_at=?
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
    # Информация о работе сегодня
    # =================================================

    def get_today_info(self, user_id):

        row = self.get_today(user_id)

        if not row:

            return {
                "started": None,
                "finished": None,
                "duration": None
            }

        started = None
        finished = None
        duration = None

        try:

            if row[1]:

                started = datetime.fromisoformat(
                    row[1]
                )

            if row[2]:

                finished = datetime.fromisoformat(
                    row[2]
                )

        except Exception:

            return {
                "started": None,
                "finished": None,
                "duration": None
            }

        if started and finished:

            difference = finished - started

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
            "finished": finished,
            "duration": duration
        }


work_logs = WorkLogRepository()