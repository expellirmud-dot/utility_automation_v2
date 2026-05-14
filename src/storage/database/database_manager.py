import sqlite3
import os

class DatabaseManager:
    DB_PATH = "data/utility_automation.db"

    @classmethod
    def get_connection(cls):
        db_dir = os.path.dirname(cls.DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return sqlite3.connect(cls.DB_PATH)

    @classmethod
    def initialize(cls):
        conn = cls.get_connection()
        with open("src/storage/database/schema.sql", "r") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
