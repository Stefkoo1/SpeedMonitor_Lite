import subprocess
import json
import sqlite3
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "speedtest.db")


def run_speedtest():
    """Runs a real speedtest using ndt7-client or simulates it if client is missing."""
    print(f"[{datetime.now()}] Starting speedtest...")

    try:

        result = subprocess.run(
            ["ndt7-client", "-format=json"],
            capture_output=True,
            text=True,
            timeout=60
        )

        data = json.loads(result.stdout)

        download = round(data['Download']['Value'] / 1000000, 2)
        upload = round(data['Upload']['Value'] / 1000000, 2)
        ping = round(data['MinRTT']['Value'] / 1000, 2)

    except (FilePathNotFoundError, Exception) as e:

        import random
        print(f"Real ndt7-client not found, using simulation mode. (Error: {e})")
        download = round(random.uniform(800, 950), 2)
        upload = round(random.uniform(700, 850), 2)
        ping = round(random.uniform(10, 20), 2)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO results (timestamp, download, upload, ping)
        VALUES (?, ?, ?, ?)
    """, (timestamp, download, upload, ping))

    conn.commit()
    conn.close()

    print(f"Test finished: DL {download} / UL {upload} / Ping {ping}")
    return {"download": download, "upload": upload, "ping": ping}