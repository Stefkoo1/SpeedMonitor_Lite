import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "speedtest.db")


def init_db():
    """Erstellt die Datenbank und die Tabelle, falls sie noch nicht existieren."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            download REAL,
            upload REAL,
            ping REAL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database created!")


if __name__ == "__main__":
    init_db()