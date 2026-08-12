from database.db import Database


def initialize_database():

    db = Database()

    db.create_tables()

    print("✅ База данных готова")