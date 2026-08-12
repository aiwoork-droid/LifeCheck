class DayItemsRepository:

    DEFAULT_ITEMS = [

        ("water", "💧 Вода"),
        ("toilet", "🚻 Туалет"),
        ("work", "💼 Работа"),
        ("prayer", "🙏 Утреннее правило"),
        ("exercise", "💪 Зарядка"),
        ("reading", "📖 Чтение"),
        ("mood", "😊 Настроение"),
        ("sleep", "😴 Сон"),
        ("weight", "⚖️ Вес")

    ]

    def __init__(self):

        from database.db import Database

        self.db = Database()

    # ==========================================
    # Создать стандартные элементы
    # ==========================================

    def create_default(self, user_id):

        for code, _ in self.DEFAULT_ITEMS:

            self.db.cursor.execute(
                """
                INSERT OR IGNORE INTO day_items
                (
                    user_id,
                    code,
                    enabled
                )
                VALUES (?, ?, 1)
                """,
                (
                    user_id,
                    code
                )
            )

        self.db.connection.commit()

    # ==========================================
    # Получить список элементов дня
    # ==========================================

    def get_items(self, user_id):

        self.create_default(user_id)

        self.db.cursor.execute(
            """
            SELECT
                code,
                enabled
            FROM day_items
            WHERE user_id=?
            ORDER BY id
            """,
            (
                user_id,
            )
        )

        rows = self.db.cursor.fetchall()

        result = []

        names = dict(self.DEFAULT_ITEMS)

        for code, enabled in rows:

            result.append({

                "code": code,
                "title": names[code],
                "enabled": bool(enabled)

            })

        return result

    # ==========================================
    # Переключить элемент
    # ==========================================

    def toggle(self, user_id, code):

        self.create_default(user_id)

        self.db.cursor.execute(
            """
            SELECT enabled
            FROM day_items
            WHERE
                user_id=?
                AND code=?
            """,
            (
                user_id,
                code
            )
        )

        row = self.db.cursor.fetchone()

        if row is None:
            return

        new_value = 0 if row[0] else 1

        self.db.cursor.execute(
            """
            UPDATE day_items
            SET enabled=?
            WHERE
                user_id=?
                AND code=?
            """,
            (
                new_value,
                user_id,
                code
            )
        )

        self.db.connection.commit()


day_items = DayItemsRepository()