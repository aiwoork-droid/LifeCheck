from datetime import date, datetime

from database.db import Database


class HabitLogRepository:

    def __init__(self):

        self.db = Database()

        # -------------------------------------------------
        # Добавляем поле completed_at в уже существующую
        # базу данных, если его ещё нет.
        # -------------------------------------------------

        try:

            self.db.cursor.execute(
                """
                ALTER TABLE habit_logs
                ADD COLUMN completed_at TEXT
                """
            )

            self.db.connection.commit()

        except Exception:

            # Поле уже существует — ничего делать не нужно.
            pass

    # -----------------------------------------------------
    # Выполнена ли привычка сегодня
    # -----------------------------------------------------

    def is_completed_today(self, habit_id):

        self.db.cursor.execute(
            """
            SELECT completed
            FROM habit_logs
            WHERE
                habit_id=?
                AND log_date=?
            """,
            (
                habit_id,
                date.today().isoformat()
            )
        )

        row = self.db.cursor.fetchone()

        if row is None:
            return False

        return bool(row[0])

    # -----------------------------------------------------
    # Время выполнения привычки сегодня
    # -----------------------------------------------------

    def get_completed_time_today(self, habit_id):

        self.db.cursor.execute(
            """
            SELECT completed_at
            FROM habit_logs
            WHERE
                habit_id=?
                AND log_date=?
                AND completed=1
            """,
            (
                habit_id,
                date.today().isoformat()
            )
        )

        row = self.db.cursor.fetchone()

        if row is None:
            return None

        if not row[0]:
            return None

        try:

            completed_at = datetime.fromisoformat(
                row[0]
            )

            return completed_at.strftime("%H:%M")

        except Exception:

            return None

    # -----------------------------------------------------
    # Отметить / снять выполнение сегодня
    # -----------------------------------------------------

    def toggle_today(self, habit_id):

        if self.is_completed_today(habit_id):

            self.db.cursor.execute(
                """
                DELETE FROM habit_logs
                WHERE
                    habit_id=?
                    AND log_date=?
                """,
                (
                    habit_id,
                    date.today().isoformat()
                )
            )

        else:

            completed_at = datetime.now().isoformat(
                timespec="seconds"
            )

            self.db.cursor.execute(
                """
                INSERT OR REPLACE INTO habit_logs
                (
                    habit_id,
                    log_date,
                    completed,
                    completed_at
                )
                VALUES (?, ?, 1, ?)
                """,
                (
                    habit_id,
                    date.today().isoformat(),
                    completed_at
                )
            )

        self.db.connection.commit()


habit_logs = HabitLogRepository()