from datetime import date, datetime

from database.db import Database


class WaterLogRepository:

    DAILY_GOAL = 8

    def __init__(self):

        self.db = Database()

    # =================================================
    # Количество стаканов сегодня
    # =================================================

    def get_today_count(self, user_id):

        self.db.cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM water_logs
            WHERE
                user_id=?
                AND log_date=?
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        row = self.db.cursor.fetchone()

        if row is None:
            return 0

        return int(row[0] or 0)

    # =================================================
    # Последнее время
    # =================================================

    def get_last_time_today(self, user_id):

        self.db.cursor.execute(
            """
            SELECT created_at
            FROM water_logs
            WHERE
                user_id=?
                AND log_date=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        row = self.db.cursor.fetchone()

        if row is None or not row[0]:
            return None

        try:

            created_at = datetime.fromisoformat(
                row[0]
            )

            return created_at.strftime("%H:%M")

        except Exception:

            return None

    # =================================================
    # Добавить стакан
    # =================================================

    def add_glass(self, user_id):

        now = datetime.now()

        self.db.cursor.execute(
            """
            INSERT INTO water_logs
            (
                user_id,
                amount,
                log_date,
                created_at
            )
            VALUES (?, 1, ?, ?)
            """,
            (
                user_id,
                date.today().isoformat(),
                now.isoformat(timespec="seconds")
            )
        )

        self.db.connection.commit()

    # =================================================
    # Убрать последний стакан
    # =================================================

    def remove_glass(self, user_id):

        self.db.cursor.execute(
            """
            SELECT id
            FROM water_logs
            WHERE
                user_id=?
                AND log_date=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        row = self.db.cursor.fetchone()

        if row is None:
            return False

        self.db.cursor.execute(
            """
            DELETE FROM water_logs
            WHERE id=?
            """,
            (row[0],)
        )

        self.db.connection.commit()

        return True


water_logs = WaterLogRepository()