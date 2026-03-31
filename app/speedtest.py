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
    print(f"[{datetime.now()}] Starte echten Speedtest...")

    download, upload, ping = 0.0, 0.0, 0.0

    try:
        # check=False verhindert Absturz bei M-Lab Fehler (Exit Code 1)
        result = subprocess.run(
            ["ndt7-client", "-format=json"],
            capture_output=True,
            text=True,
            timeout=90,
            check=False
        )

        for line in result.stdout.splitlines():
            if not line.strip(): continue
            try:
                data = json.loads(line)

                # M-Lab Sperre (Rate Limit) erkennen
                if 'Value' in data and isinstance(data['Value'], dict) and 'Failure' in data['Value']:
                    print(f"M-Lab INFO: {data['Value']['Failure']}")
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
            print(f"[{timestamp}] Test erfolgreich: DL {download}, UL {upload}")
            return {"status": "success", "data": {"download": download, "upload": upload, "ping": ping}}
        else:
            msg = "Keine Messdaten erhalten (evtl. M-Lab Sperre aktiv)."
            print(f"[{datetime.now()}] Test fehlgeschlagen: {msg}")
            return {"status": "error", "message": msg}

    except subprocess.TimeoutExpired:
        msg = "Timeout beim Speedtest (länger als 90s)."
        print(f"[{datetime.now()}] {msg}")
        return {"status": "error", "message": msg}
    except Exception as e:
        msg = str(e)
        print(f"[{datetime.now()}] Unerwarteter Fehler: {msg}")
        return {"status": "error", "message": msg}