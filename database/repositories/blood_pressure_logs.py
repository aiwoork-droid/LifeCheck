from datetime import date, datetime

from database.db import Database


class BloodPressureLogRepository:

    def __init__(self):

        self.db = Database()

    # =================================================
    # Количество измерений сегодня
    # =================================================

    def get_today_count(self, user_id):

        self.db.cursor.execute(
            """
            SELECT COUNT(*)
            FROM blood_pressure_logs
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
    # Все измерения сегодня
    # =================================================

    def get_today_measurements(self, user_id):

        self.db.cursor.execute(
            """
            SELECT
                systolic,
                diastolic,
                pulse,
                created_at
            FROM blood_pressure_logs
            WHERE
                user_id=?
                AND log_date=?
            ORDER BY id
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        rows = self.db.cursor.fetchall()

        result = []

        for row in rows:

            systolic = row[0]
            diastolic = row[1]
            pulse = row[2]
            created_at = row[3]

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
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "pulse": pulse,
                    "time": time_text
                }
            )

        return result

    # =================================================
    # Последнее измерение сегодня
    # =================================================

    def get_last_measurement(self, user_id):

        self.db.cursor.execute(
            """
            SELECT
                systolic,
                diastolic,
                pulse,
                created_at
            FROM blood_pressure_logs
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
            return None

        systolic = row[0]
        diastolic = row[1]
        pulse = row[2]
        created_at = row[3]

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

        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "time": time_text
        }

    # =================================================
    # Добавить измерение
    # =================================================

    def add_measurement(
        self,
        user_id,
        systolic,
        diastolic,
        pulse
    ):

        now = datetime.now()

        self.db.cursor.execute(
            """
            INSERT INTO blood_pressure_logs
            (
                user_id,
                log_date,
                systolic,
                diastolic,
                pulse,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                date.today().isoformat(),
                systolic,
                diastolic,
                pulse,
                now.isoformat(
                    timespec="seconds"
                )
            )
        )

        self.db.connection.commit()

    # =================================================
    # Удалить последнее измерение сегодня
    # =================================================

    def remove_last_measurement(self, user_id):

        self.db.cursor.execute(
            """
            SELECT id
            FROM blood_pressure_logs
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
            DELETE FROM blood_pressure_logs
            WHERE id=?
            """,
            (
                row[0],
            )
        )

        self.db.connection.commit()

        return True


blood_pressure_logs = BloodPressureLogRepository()