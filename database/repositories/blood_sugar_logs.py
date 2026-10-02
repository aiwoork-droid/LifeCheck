from datetime import date, datetime

from database.db import Database


class BloodSugarLogRepository:

    MEAL_LABELS = {
        "before": "до еды",
        "after": "после еды",
        "between": "между приёмами (2 ч)"
    }

    def __init__(self):
        self.db = Database()

    def get_today_count(self, user_id):
        self.db.cursor.execute(
            """
            SELECT COUNT(*)
            FROM blood_sugar_logs
            WHERE
                user_id = ?
                AND log_date = ?
            """,
            (user_id, date.today().isoformat())
        )
        row = self.db.cursor.fetchone()

        if row is None:
            return 0

        return int(row[0] or 0)

    def get_today_measurements(self, user_id):
        self.db.cursor.execute(
            """
            SELECT
                id,
                value,
                meal_context,
                created_at
            FROM blood_sugar_logs
            WHERE
                user_id = ?
                AND log_date = ?
            ORDER BY id
            """,
            (user_id, date.today().isoformat())
        )

        rows = self.db.cursor.fetchall()

        result = []

        for row in rows:

            time_text = None

            if row[3]:

                try:
                    time_text = datetime.fromisoformat(
                        row[3]
                    ).strftime("%H:%M")

                except Exception:
                    time_text = None

            result.append({
                "id": row[0],
                "value": row[1],
                "meal_context": row[2],
                "meal_label": self.MEAL_LABELS.get(
                    row[2],
                    row[2] or "—"
                ),
                "time": time_text
            })

        return result

    def add_measurement(
        self,
        user_id,
        value,
        meal_context,
        at=None
    ):

        if meal_context not in self.MEAL_LABELS:
            return False

        try:
            value = float(
                str(value).replace(",", ".")
            )

        except (TypeError, ValueError):
            return False

        if value < 1.0 or value > 40.0:
            return False

        if at is None:
            at = datetime.now()

        self.db.cursor.execute(
            """
            INSERT INTO blood_sugar_logs
            (
                user_id,
                log_date,
                value,
                meal_context,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                date.today().isoformat(),
                value,
                meal_context,
                at.isoformat(timespec="seconds")
            )
        )

        self.db.connection.commit()

        return True

    def remove_last_measurement(self, user_id):

        self.db.cursor.execute(
            """
            SELECT id
            FROM blood_sugar_logs
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
            "DELETE FROM blood_sugar_logs WHERE id = ?",
            (row[0],)
        )

        self.db.connection.commit()

        return True


blood_sugar_logs = BloodSugarLogRepository()
