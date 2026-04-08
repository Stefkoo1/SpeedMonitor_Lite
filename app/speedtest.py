import subprocess
import json
import sqlite3
from datetime import datetime
from app.database import DB_PATH, init_db


def run_speedtest():
    init_db()
    print(f"[{datetime.now()}] Starte Speedtest...")

    download, upload, ping = 0.0, 0.0, 0.0

    try:
        result = subprocess.run(
            ["ndt7-client", "-format=json"],
            capture_output=True,
            text=True,
            timeout=90,
            check=False
        )

        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if 'Value' in data and isinstance(data['Value'], dict) and 'Failure' in data['Value']:
                    print(f"M-Lab INFO: {data['Value']['Failure']}")
                    continue
                if 'Download' in data and 'Throughput' in data['Download']:
                    download = round(data['Download']['Throughput']['Value'], 2)
                    upload = round(data['Upload']['Throughput']['Value'], 2)
                    ping = round(data['Download']['Latency']['Value'], 2)
            except Exception:
                continue

        if download > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO results (timestamp, download, upload, ping) VALUES (?, ?, ?, ?)",
                (timestamp, download, upload, ping)
            )
            conn.commit()
            conn.close()
            print(f"[{timestamp}] Test OK: DL={download} Mbps, UL={upload} Mbps, Ping={ping} ms")
            return {"status": "success", "data": {"download": download, "upload": upload, "ping": ping}}
        else:
            msg = "Keine Messdaten erhalten (M-Lab Rate Limit aktiv oder keine Verbindung)."
            print(f"[{datetime.now()}] {msg}")
            return {"status": "error", "message": msg}

    except subprocess.TimeoutExpired:
        msg = "Speedtest Timeout (>90s)."
        print(f"[{datetime.now()}] {msg}")
        return {"status": "error", "message": msg}
    except Exception as e:
        msg = str(e)
        print(f"[{datetime.now()}] Unerwarteter Fehler: {msg}")
        return {"status": "error", "message": msg}
