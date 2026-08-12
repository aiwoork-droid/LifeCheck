from datetime import datetime

from database.db import Database


class HabitRepository:

    def __init__(self):
        self.db = Database()

    def add_habit(self, user_id, title):

        self.db.cursor.execute("""
            INSERT INTO habits
            (
                user_id,
                title,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            title,
            datetime.now().isoformat()
        ))

        self.db.connection.commit()

    def get_habits(self, user_id):

        self.db.cursor.execute("""
            SELECT
                id,
                title,
                is_active
            FROM habits
            WHERE user_id=?
            ORDER BY id
        """, (user_id,))

        return self.db.cursor.fetchall()

    def habit_exists(self, user_id, title):

        self.db.cursor.execute("""
            SELECT id
            FROM habits
            WHERE
                user_id=?
                AND title=?
        """, (
            user_id,
            title
        ))

        return self.db.cursor.fetchone() is not None

    def delete_habit(self, habit_id):

        self.db.cursor.execute("""
            DELETE FROM habits
            WHERE id=?
        """, (habit_id,))

        self.db.connection.commit()


habits = HabitRepository()