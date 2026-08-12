import sqlite3
import os


DATABASE_NAME = "database/lifecheck.db"


class Database:

    def __init__(self):

        os.makedirs(
            "database",
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            DATABASE_NAME,
            check_same_thread=False
        )

        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        # ==================================================
        # Пользователи
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT,
            last_activity TEXT
        )
        """)

        # ==================================================
        # Состояние пользователя
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            current_screen TEXT
        )
        """)

        # ==================================================
        # Привычки
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)

        # ==================================================
        # Выполнение привычек
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER,
            log_date TEXT,
            completed INTEGER DEFAULT 1,
            completed_at TEXT,
            UNIQUE(habit_id, log_date)
        )
        """)

        # ==================================================
        # Вода
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER DEFAULT 1,
            log_date TEXT,
            created_at TEXT
        )
        """)

        # ==================================================
        # Туалет
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS toilet_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            created_at TEXT,
            stool_type TEXT
        )
        """)

        # ==================================================
        # Сон
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sleep_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sleep_date TEXT,
            sleep_started_at TEXT,
            wake_up_at TEXT
        )
        """)

        # ==================================================
        # Работа
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            work_date TEXT,
            work_started_at TEXT,
            work_finished_at TEXT
        )
        """)

        # ==================================================
        # Мигрень
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS migraine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            migraine_date TEXT,
            intensity INTEGER,
            created_at TEXT,
            UNIQUE(user_id, migraine_date)
        )
        """)

        # ==================================================
        # Давление
        # ==================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_pressure_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            systolic INTEGER,
            diastolic INTEGER,
            pulse INTEGER,
            created_at TEXT
        )
        """)

        self.connection.commit()