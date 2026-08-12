from datetime import date, datetime

from database.db import Database


class MigraineLogRepository:

    def __init__(self):

        self.db = Database()

    # ==================================================
    # Получить запись о мигрени за сегодня
    # ==================================================

    def get_today(self, user_id):

        self.db.cursor.execute(
            """
            SELECT
                id,
                intensity,
                created_at
            FROM migraine_logs
            WHERE
                user_id = ?
                AND migraine_date = ?
            LIMIT 1
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        return self.db.cursor.fetchone()

    # ==================================================
    # Проверить, была ли мигрень сегодня
    # ==================================================

    def has_today(self, user_id):

        return self.get_today(user_id) is not None

    # ==================================================
    # Добавить мигрень
    # ==================================================

    def add_migraine(self, user_id, intensity):

        # Допустимая шкала:
        # 1 — очень слабо
        # 10 — очень сильно

        if not isinstance(intensity, int):
            return False

        if intensity < 1 or intensity > 10:
            return False

        now = datetime.now()

        existing = self.get_today(user_id)

        # ----------------------------------------------
        # Если запись уже есть — обновляем силу
        # ----------------------------------------------

        if existing:

            self.db.cursor.execute(
                """
                UPDATE migraine_logs
                SET
                    intensity = ?,
                    created_at = ?
                WHERE id = ?
                """,
                (
                    intensity,
                    now.isoformat(timespec="seconds"),
                    existing[0]
                )
            )

        # ----------------------------------------------
        # Если записи нет — создаём
        # ----------------------------------------------

        else:

            self.db.cursor.execute(
                """
                INSERT INTO migraine_logs
                (
                    user_id,
                    migraine_date,
                    intensity,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    date.today().isoformat(),
                    intensity,
                    now.isoformat(timespec="seconds")
                )
            )

        self.db.connection.commit()

        return True

    # ==================================================
    # Удалить мигрень за сегодня
    # ==================================================

    def remove_today(self, user_id):

        self.db.cursor.execute(
            """
            DELETE FROM migraine_logs
            WHERE
                user_id = ?
                AND migraine_date = ?
            """,
            (
                user_id,
                date.today().isoformat()
            )
        )

        self.db.connection.commit()

        return True

    # ==================================================
    # Получить информацию для экрана "Сегодня"
    # ==================================================

    def get_today_info(self, user_id):

        row = self.get_today(user_id)

        if not row:

            return {
                "exists": False,
                "intensity": None,
                "time": None
            }

        time_text = None

        if row[2]:

            try:

                created_at = datetime.fromisoformat(
                    row[2]
                )

                time_text = created_at.strftime(
                    "%H:%M"
                )

            except Exception:

                time_text = None

        return {
            "exists": True,
            "intensity": row[1],
            "time": time_text
        }


migraine_logs = MigraineLogRepository()