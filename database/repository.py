from datetime import datetime

from database.db import Database


class UserRepository:

    def __init__(self):
        self.db = Database()

    # =====================================================
    # Пользователи
    # =====================================================

    def create_user(self, user_id, first_name, last_name):

        self.db.cursor.execute("""
            INSERT OR IGNORE INTO users
            (
                user_id,
                first_name,
                last_name,
                created_at,
                last_activity
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            first_name,
            last_name,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        self.db.connection.commit()

        self.create_state(user_id)

    def update_activity(self, user_id):

        self.db.cursor.execute("""
            UPDATE users
            SET last_activity=?
            WHERE user_id=?
        """, (
            datetime.now().isoformat(),
            user_id
        ))

        self.db.connection.commit()

    def user_exists(self, user_id):

        self.db.cursor.execute("""
            SELECT id
            FROM users
            WHERE user_id=?
        """, (user_id,))

        return self.db.cursor.fetchone() is not None

    # =====================================================
    # Состояние пользователя
    # =====================================================

    def create_state(self, user_id):

        self.db.cursor.execute("""
            INSERT OR IGNORE INTO user_states
            (
                user_id,
                current_screen
            )
            VALUES (?, ?)
        """, (
            user_id,
            "menu"
        ))

        self.db.connection.commit()

    def get_screen(self, user_id):

        self.create_state(user_id)

        self.db.cursor.execute("""
            SELECT current_screen
            FROM user_states
            WHERE user_id=?
        """, (user_id,))

        result = self.db.cursor.fetchone()

        if result:
            return result[0]

        return "menu"

    def set_screen(self, user_id, screen):

        self.create_state(user_id)

        self.db.cursor.execute("""
            UPDATE user_states
            SET current_screen=?
            WHERE user_id=?
        """, (
            screen,
            user_id
        ))

        self.db.connection.commit()


repository = UserRepository()