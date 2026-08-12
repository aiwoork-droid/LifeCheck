from datetime import date, datetime

from database.db import Database


class ToiletLogRepository:

    def __init__(self):

        self.db = Database()

    # =================================================
    # Количество посещений сегодня
    # =================================================

    def get_today_count(self, user_id):

        self.db.cursor.execute(
            """
            SELECT COUNT(*)
            FROM toilet_logs
            WHERE
                user_id = ?
                AND log_date = ?
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
    # Последнее время сегодня
    # =================================================

    def get_last_time_today(self, user_id):

        self.db.cursor.execute(
            """
            SELECT created_at
            FROM toilet_logs
            WHERE
                user_id = ?
                AND log_date = ?
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
    # Все посещения сегодня
    # =================================================

    def get_today_visits(self, user_id):

        self.db.cursor.execute(
            """
            SELECT
                id,
                stool_type,
                created_at
            FROM toilet_logs
            WHERE
                user_id = ?
                AND log_date = ?
            ORDER BY id ASC
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        rows = self.db.cursor.fetchall()

        result = []

        for row in rows:

            visit_id = row[0]
            stool_type = row[1]
            created_at = row[2]

            time_text = None

            if created_at:

                try:

                    created_at_dt = datetime.fromisoformat(
                        created_at
                    )

                    time_text = created_at_dt.strftime(
                        "%H:%M"
                    )

                except Exception:

                    time_text = None

            result.append(
                {
                    "id": visit_id,
                    "stool_type": stool_type,
                    "time": time_text
                }
            )

        return result

    # =================================================
    # Добавить посещение
    # =================================================

    def add_visit(
        self,
        user_id,
        stool_type
    ):

        allowed_types = (
            "жидко",
            "мягко",
            "нормально",
            "запор"
        )

        if stool_type not in allowed_types:

            return False

        now = datetime.now()

        self.db.cursor.execute(
            """
            INSERT INTO toilet_logs
            (
                user_id,
                log_date,
                stool_type,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                date.today().isoformat(),
                stool_type,
                now.isoformat(
                    timespec="seconds"
                )
            )
        )

        self.db.connection.commit()

        return True

    # =================================================
    # Удалить последнее посещение
    # =================================================

    def remove_visit(self, user_id):

        self.db.cursor.execute(
            """
            SELECT id
            FROM toilet_logs
            WHERE
                user_id = ?
                AND log_date = ?
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
            DELETE FROM toilet_logs
            WHERE id = ?
            """,
            (
                row[0],
            )
        )

        self.db.connection.commit()

        return True


toilet_logs = ToiletLogRepository()