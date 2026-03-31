import subprocess
import json
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "speedtest.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            download REAL,
            upload REAL,
            ping REAL
        )
    """)
    conn.commit()
    conn.close()


def run_speedtest():
    init_db()
    print(f"[{datetime.now()}] Starte  Speedtest...")

    download, upload, ping = 0, 0, 0

    try:
        result = subprocess.run(
            ["ndt7-client", "-format=json"],
            capture_output=True,
            text=True,
            timeout=90
        )

        for line in result.stdout.splitlines():
            if not line.strip(): continue
            try:
                data = json.loads(line)


                if 'Value' in data and isinstance(data['Value'], dict) and 'Failure' in data['Value']:
                    print(f"M-Lab ERROR: {data['Value']['Failure']}")
                    continue

                if 'Download' in data and 'Throughput' in data['Download']:
                    download = round(data['Download']['Throughput']['Value'], 2)
                    upload = round(data['Upload']['Throughput']['Value'], 2)
                    ping = round(data['Download']['Latency']['Value'], 2)
            except:
                continue


        if download > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO results (timestamp, download, upload, ping)
                VALUES (?, ?, ?, ?)
            """, (timestamp, download, upload, ping))
            conn.commit()
            conn.close()
            print(f"[{timestamp}] Test erfolgreich gespeichert.")
            return True
    except Exception as e:
        print(f"Test abgebrochen oder Fehler: {e}")

    return False